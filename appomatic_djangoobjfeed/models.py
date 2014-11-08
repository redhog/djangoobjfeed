# -*- coding: utf-8 -*-
import datetime
import threading
import django.db.models
import django.contrib.auth.models
import django.template
import django.template.loader
from django.conf import settings
from django.db.models import Q
import fcdjangoutils.modelhelpers
import fcdjangoutils.signalautoconnectmodel
import appomatic_renderable.models
import fcdjangoutils.middleware
import fcdjangoutils.responseutils
import contextlib
try:
    import pinax.apps.tribes.models as tribemodels
    import pinax.apps.blog.models as blogmodels
    import pinax.apps.photos.models as photosmodels
except:
    tribemodels = None
    blogmodels = None
    photosmodels = None
try:
    import microblogging.models as microbloggingmodels
except:
    microbloggingmodels = None
try:
    import friends.models as friendsmodels
except:
    friendsmodels = None


def get_return_address(request):
    if '_next' in request.POST:
        return request.POST['_next']
    if '_next' in request.GET:
        return request.GET['_next']
    if 'HTTP_REFERER' in request.META:
        return request.META['HTTP_REFERER']
    return '/'


# Feeds

class ObjFeed(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, appomatic_renderable.models.Renderable):
    class __metaclass__(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__):
        def __init__(cls, *arg, **kw):
            fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__.__init__(cls, *arg, **kw)
            if cls.__name__ != 'ObjFeed' and cls.owner is not None:
                django.db.models.signals.post_save.connect(cls.owner_post_save, sender=cls.owner.field.rel.to)

    @classmethod
    def owner_post_save(cls, sender, instance, **kwargs):
        # Try around this as OneToOneField are stupid and can't handle null in a sensible way
        try:
            if instance.feed is not None:
                return
        except:
            pass
        cls(owner=instance).save()

    def entry_added(self, entry):
        pass

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def owner(self): raise fcdjangoutils.modelhelpers.MustBeOverriddenError

    @fcdjangoutils.modelhelpers.subclassproxy
    def __unicode__(self):
        return "Feed for %s" % (self.owner,)

    @property
    def entries(self):
        return self.all_entries.filter(obj_feed_entry__posted_at__lte = datetime.datetime.now()).order_by('-obj_feed_entry__posted_at')

    @property
    def new_entries(self):
        return self.entries.filter(seen=False)

    @property
    def own_entries(self):
        return self.entries

    def allowed_to_post(self, user=None):
        return False

    def handle__post(self, request, style):
        Message(
            feed = self,
            author = request.user,
            content = request.POST[self.fieldname + 'content']
            ).save()

        raise fcdjangoutils.responseutils.EarlyResponseException(
            django.shortcuts.redirect(get_return_address(request)))

class NamedFeed(ObjFeed):
    owner = None
    name = django.db.models.CharField(max_length=255)
    allow_public_postings = django.db.models.BooleanField()

    def __unicode__(self):
        return "Feed called %s" % (self.name,)

    def allowed_to_post(self, user=None):
        return self.allow_public_postings

    @property
    def own_entries(self):
        return self.entries


class UserFeed(ObjFeed):
    owner = django.db.models.OneToOneField(django.contrib.auth.models.User, primary_key=True, related_name="feed")
    send_email = django.db.models.BooleanField(default = True)

    def allowed_to_post(self, user=None):
        if user is None: user = fcdjangoutils.middleware.get_request().user
        if self.owner.id == user.id:
            return True
        try:
            return self.owner.subclassobject.check_permission(user, 'wall_posts')
        except:
            return user.id in set(u.id for u in friends.models.friend_set_for(self.owner))

    @property
    def own_entries(self):
        return self.entries.filter(Q(obj_feed_entry__author__id = self.owner.id) | Q(obj_feed_entry__messagefeedentry__obj__feed__id = self.id))

    def entry_added(self, entry):
        obj_feed_entry = entry.obj_feed_entry.subclassobject
        author = obj_feed_entry.get_author_from_obj(obj_feed_entry)
        if author.id == self.owner.id:
            entry.see()
            print "Not sending email to author"
            return

        if not self.send_email:
            print "User doesn't want email"
            return

        with FeedEntry.invisible():
            django.core.mail.send_mail(
                entry.render(style="title"),
                entry.render(style="inline.txt"),
                settings.DEFAULT_FROM_EMAIL,
                [self.owner.email],
                fail_silently=False)


if tribemodels:
    class TribeFeed(ObjFeed):
        owner = django.db.models.OneToOneField(tribemodels.Tribe, primary_key=True, related_name="feed")

        def allowed_to_post(self, user):
            # Really, check for membership here
            return False

# Subscriptions

class ObjFeedSubscription(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel):
    feed = django.db.models.ForeignKey(ObjFeed, related_name="subscriptions")

    def is_for(self, feed_entry):
        # Fixme: Some tag stuff here?
        return True

class UserFeedSubscription(ObjFeedSubscription):
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="subscribed_on_by_feeds")

    def __unicode__(self):
        return "%s subscribes to %s" % (self.feed, self.author)


# Feed entries

class FeedEntryManager(django.db.models.Manager):
    def get_query_set(self):
        return django.db.models.Manager.get_query_set(self).order_by("obj_feed_entry__posted_at")

class FeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, appomatic_renderable.models.Renderable):
    threadLocal = threading.local()

    class Meta:
        ordering = ('obj_feed_entry__posted_at',)

    objects = FeedEntryManager()
    feed = django.db.models.ForeignKey("ObjFeed", related_name="all_entries")
    obj_feed_entry = django.db.models.ForeignKey("ObjFeedEntry", related_name="feed_entry")
    seen = django.db.models.BooleanField(default=False)


    @classmethod
    def on_post_save(cls, sender, instance, **kwargs):
        instance.feed.subclassobject.entry_added(instance)

    @classmethod
    @contextlib.contextmanager
    def invisible(cls):
        cls.threadLocal.invisible = True
        yield
        cls.threadLocal.invisible = False

    def see(self):
        if not self.seen and not getattr(self.threadLocal, "invisible", False):
            self.seen = True
            self.save()
        return ""

    def render(self, *arg, **kw):
        self.see()
        return appomatic_renderable.models.Renderable.render(self, *arg, **kw)

    @property
    def display_name(self):
        return self.obj_feed_entry.subclassobject.display_name

    # Very very spartan so it can't break into infinite recursion hell... I.e. DONT't call templates here!!!
    def __repr__(self):
        try:
            return "%s: %s posted to %s" % (type(self), self.obj_feed_entry.author, self.feed)
        except:
            return "FeedEntry"

    def __unicode__(self):
        return u"FeedEntry"

    def render__title(self, request, context):
        return self.obj_feed_entry.render(request=request, style="title")

    @fcdjangoutils.modelhelpers.subclassproxy
    def get_absolute_url(self):
        if hasattr(self.obj_feed_entry.obj, 'get_absolute_url'):
            return self.obj_feed_entry.obj.get_absolute_url()
        else:
            return 'http://' + django.contrib.sites.models.Site.objects.get_current().domain + django.core.urlresolvers.reverse(
                'appomatic_djangoobjfeed.views.get_feed_entry',
                kwargs={"feed_entry_id":self.id})


class CommentFeedEntryManager(django.db.models.Manager):
    def get_query_set(self):
        return django.db.models.Manager.get_query_set(self).order_by("posted_at")

class CommentFeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, appomatic_renderable.models.Renderable):
    objects = CommentFeedEntryManager()

    posted_at = django.db.models.DateTimeField(auto_now=True)
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="feed_comment_postings")

    comment_on_feed_entry = django.db.models.ForeignKey("ObjFeedEntry", related_name="comments_in", null=True, blank=True)
    comment_on_comment = django.db.models.ForeignKey("CommentFeedEntry", related_name="comments_in", null=True, blank=True)
    content = django.db.models.TextField()

    is_comment = True

    @property
    def display_name(self):
        return type(self).__name__[:-len('FeedEntry')]

    def handle__delete(self, request, style):
        if request.user.id != self.author.id:
            django.contrib.messages.error(request, 'Access violation')
            return {}

        self.delete()

        raise fcdjangoutils.responseutils.EarlyResponseException(
            django.shortcuts.redirect(get_return_address(request)))

    def handle__update(self, request, style):
        if request.user.id != self.author.id:
            django.contrib.messages.error(request, 'Access violation')
            return {}

        self.content = request.POST[self.fieldname + 'content']
        self.save()

        raise fcdjangoutils.responseutils.EarlyResponseException(
            django.shortcuts.redirect(get_return_address(request)))


# Feed entry adaptors for objects

class ObjFeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, appomatic_renderable.models.Renderable):
    class __metaclass__(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__):
        def __init__(cls, *arg, **kw):
            fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__.__init__(cls, *arg, **kw)
            if cls.__name__ != 'ObjFeedEntry':
                django.db.models.signals.post_save.connect(cls.obj_post_save, sender=cls.obj.field.rel.to)

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def obj(self): raise fcdjangoutils.modelhelpers.MustBeOverriddenError
    posted_at = django.db.models.DateTimeField(blank=True)
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="feed_postings")

    @classmethod
    def on_pre_save(cls, sender, instance, **kwargs):
        if instance.posted_at is None:
            instance.posted_at = datetime.datetime.now()

    @classmethod
    def get_author_from_obj(cls, instance):
        raise NotImplementedError

    @classmethod
    def clear_feeds(cls, instance, author):
        pass

    @classmethod
    def copy_feeds(cls, instance, author):
        for method in dir(cls):
            if method.endswith("_feeds_for_obj"):
                for is_for, feed in getattr(cls, method)(instance, author):
                    yield is_for, feed

    @classmethod
    def subscription_feeds_for_obj(cls, instance, author):
        for subscription in author.subscribed_on_by_feeds.all():
            yield (subscription.is_for, subscription.feed.superclassobject)

    @classmethod
    def own_feeds_for_obj(cls, instance, author):
        yield lambda feed_entry: True, author.feed.superclassobject

    @classmethod
    def friend_feeds_for_obj(cls, instance, author):
        # Slightly ugly test...
        if hasattr(author, 'friends'):
            for friend in friends.models.friend_set_for(author):
                if hasattr(friend, 'feed'):
                    yield lambda feed_entry: True, friend.feed.superclassobject

    @classmethod
    def obj_is_new(cls, instance):
        return instance.feed_entry.count() == 0

    @classmethod
    def obj_needs_feed_entry(cls, instance):
        return cls.obj_is_new(instance)

    @classmethod
    def obj_post_save(cls, sender, instance, **kwargs):
        # Maybe we want changes to objects too? Then uncomment this...
        if not cls.obj_needs_feed_entry(instance):
            return
        author = cls.get_author_from_obj(instance)
        obj_feed_entries = instance.feed_entry.all()
        if len(obj_feed_entries) > 0:
            obj_feed_entry = obj_feed_entries[0]
        else:
            obj_feed_entry = cls(author = author,
                                 obj = instance)
        obj_feed_entry.save()

        cls.clear_feeds(instance, author)
        done = set(feed_entry.feed.id for feed_entry in obj_feed_entry.feed_entry.all())
        for matches_subscription, feed in cls.copy_feeds(instance, author):
            if feed.id in done:
                continue
            done.add(feed.id)
            feed_entry = FeedEntry(obj_feed_entry=obj_feed_entry,
                                   feed=feed)
            if matches_subscription(feed_entry):
                feed_entry.save()

    # Very very spartan so it can't break into infinite recursion hell... I.e. DONT't call templates here!!!
    def __repr__(self):
        return "%s by %s" % (type(self), self.author)

    def __unicode__(self):
        return unicode(FeedEntry(obj_feed_entry=self))

    @fcdjangoutils.modelhelpers.subclassproxy
    def get_absolute_url(self):
        return self.obj.get_absolute_url()

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def title(self):
        return getattr(self.obj, 'title', getattr(self.obj, 'name', None))

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def display_name(self):
        return type(self).__name__[:-len('FeedEntry')]

    def allowed_to_post_comment(self, user = None):
        if user is None: user = fcdjangoutils.middleware.get_request().user
        author = self.author
        author = getattr(author, 'subclassobject', author)
        if hasattr(author, 'allowed_to_post_comment'):
            return author.allowed_to_post_comment(self, user)
        return True

    def handle__post(self, request, style):
        if not self.allowed_to_post_comment(request.user):
            django.contrib.messages.error(request, 'Access violation')
            return {}
        CommentFeedEntry(
            author = request.user,
            comment_on_feed_entry = self,
            content = request.POST[self.fieldname + 'content']
            ).save()

        raise fcdjangoutils.responseutils.EarlyResponseException(
            django.shortcuts.redirect(get_return_address(request)))


# Feed entry adapers

class Message(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel):
    feed = django.db.models.ForeignKey(ObjFeed, related_name="messages")
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="messages")
    content = django.db.models.TextField()

class MessageFeedEntry(ObjFeedEntry):
    obj = django.db.models.ForeignKey(Message, related_name='feed_entry')

    @classmethod
    def get_author_from_obj(cls, obj):
        return obj.author

    @classmethod
    def feed_feeds_for_obj(cls, instance, author):
        yield lambda feed_entry: True, instance.feed.superclassobject

    def render__title(self, request, context):
        return self.obj.content.split("\n", 1)[0]


if microbloggingmodels:
    class TweetFeedEntry(ObjFeedEntry):
        obj = django.db.models.ForeignKey(microbloggingmodels.Tweet, related_name='feed_entry')

        @classmethod
        def get_author_from_obj(cls, obj):
            return obj.sender

if blogmodels:
    class BlogFeedEntry(ObjFeedEntry):
        obj = django.db.models.ForeignKey(blogmodels.Post, related_name='feed_entry')

        @classmethod
        def get_author_from_obj(cls, obj):
            return obj.author

if photosmodels:
    class ImageFeedEntry(ObjFeedEntry):
        obj = django.db.models.ForeignKey(photosmodels.Image, related_name='feed_entry')

        @classmethod
        def get_author_from_obj(cls, obj):
            return obj.member

