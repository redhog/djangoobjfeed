# -*- coding: utf-8 -*-
import django.db.models
import django.contrib.auth.models
import pinax.apps.tribes.models
import microblogging.models
import pinax.apps.blog.models
import pinax.apps.photos.models
import fcdjangoutils.modelhelpers
import fcdjangoutils.signalautoconnectmodel
import django.template
import django.template.loader
import datetime
import friends.models
from django.db.models import Q

# Feeds

class ObjFeed(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, fcdjangoutils.modelhelpers.SubclasModelMixin):
    class __metaclass__(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__):
        def __init__(cls, *arg, **kw):
            fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel.__metaclass__.__init__(cls, *arg, **kw)
            if cls.__name__ != 'ObjFeed' and cls.owner is not None:
                django.db.models.signals.post_save.connect(cls.obj_post_save, sender=cls.owner.field.rel.to)

    @classmethod
    def obj_post_save(cls, sender, instance, **kwargs):
        # Try around this as OneToOneField are stupid and can't handle null in a sensible way
        try:
            if instance.feed is not None:
                return
        except:
            pass
        cls(owner=instance).save()

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def owner(self): raise fcdjangoutils.modelhelpers.MustBeOverriddenError

    @fcdjangoutils.modelhelpers.subclassproxy
    def __unicode__(self):
        return "Feed for %s" % (self.owner,)

    @property
    def entries(self):
        return self.all_entries.filter(obj_feed_entry__posted_at__lte = datetime.datetime.now())

    @property
    def own_entries(self):
        return self.entries

    def allowed_to_post(self, user):
        return False

class NamedFeed(ObjFeed):
    owner = None
    name = django.db.models.CharField(max_length=255)
    allow_public_postings = django.db.models.BooleanField()

    def __unicode__(self):
        return "Feed called %s" % (self.name,)

    def allowed_to_post(self, user):
        return self.allow_public_postings

    @property
    def own_entries(self):
        return self.entries


class UserFeed(ObjFeed):
    owner = django.db.models.OneToOneField(django.contrib.auth.models.User, primary_key=True, related_name="feed")

    def allowed_to_post(self, user):
        if self.owner.id == user.id:
            return True
        return user.id in set(u.id for u in friends.models.friend_set_for(self.owner))

    @property
    def own_entries(self):
        return self.entries.filter(Q(obj_feed_entry__author__id = self.owner.id) | Q(obj_feed_entry__messagefeedentry__obj__feed__id = self.id))


class TribeFeed(ObjFeed):
    owner = django.db.models.OneToOneField(pinax.apps.tribes.models.Tribe, primary_key=True, related_name="feed")

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

class FeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, fcdjangoutils.modelhelpers.SubclasModelMixin):
    objects = FeedEntryManager()
    feed = django.db.models.ForeignKey("ObjFeed", related_name="all_entries")
    obj_feed_entry = django.db.models.ForeignKey("ObjFeedEntry", related_name="feed_entry")

    @property
    def display_name(self):
        return self.obj_feed_entry.subclassobject.display_name

    def render(self, format = 'html', context = None):
        if context is None:
            context = django.template.Context({})
        try:
            context.push()
            context['feed_entry'] = self
            from fcdjangoutils.timer import Timer
            with Timer('entry'):
                return django.template.loader.get_template(self.obj_feed_entry.template % {'format':format}
                                                           ).render(context)
        finally:
            context.pop()

    # Very very spartan so it can't break into infinite recursion hell... I.e. DONT't call templates here!!!
    def __repr__(self):
        try:
            return "%s: %s posted to %s" % (type(self), self.obj_feed_entry.author, self.feed)
        except:
            return "FeedEntry"

    def __unicode__(self):
        return u"FeedEntry"

class CommentFeedEntryManager(django.db.models.Manager):
    def get_query_set(self):
        return django.db.models.Manager.get_query_set(self).order_by("posted_at")

class CommentFeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, fcdjangoutils.modelhelpers.SubclasModelMixin):
    objects = CommentFeedEntryManager()

    posted_at = django.db.models.DateTimeField(auto_now=True)
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="feed_comment_postings")

    comment_on_feed_entry = django.db.models.ForeignKey("ObjFeedEntry", related_name="comments_in", null=True, blank=True)
    comment_on_comment = django.db.models.ForeignKey("CommentFeedEntry", related_name="comments_in", null=True, blank=True)
    content = django.db.models.TextField()

    template = "djangoobjfeed/render_comment_entry.%(format)s"

    is_comment = True

    @property
    def display_name(self):
        return type(self).__name__[:-len('FeedEntry')]        

    def render(self, format = 'html', context = None):
        class Dummy(object):
            pass
        context.push()
        try:
            context['feed_entry'] = Dummy()
            context['feed_entry'].obj_feed_entry = self
            return django.template.loader.get_template(self.template % {'format':format}
                                                       ).render(context)
        finally:
            context.pop()

# Feed entry adaptors for objects

class ObjFeedEntry(fcdjangoutils.signalautoconnectmodel.SignalAutoConnectModel, fcdjangoutils.modelhelpers.SubclasModelMixin):
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

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def template(self):
        return "djangoobjfeed/render_feed_entry.%(format)s"

    def allowed_to_post_comment(self, user):
        author = self.author
        author = getattr(author, 'subclassobject', author)
        if hasattr(author, 'allowed_to_post_comment'):
            return author.allowed_to_post_comment(self, user)
        return True

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

    template = "djangoobjfeed/render_message_entry.%(format)s"

    @classmethod
    def feed_feeds_for_obj(cls, instance, author):
        yield lambda feed_entry: True, instance.feed.superclassobject

class TweetFeedEntry(ObjFeedEntry):
    obj = django.db.models.ForeignKey(microblogging.models.Tweet, related_name='feed_entry')

    @classmethod
    def get_author_from_obj(cls, obj):
        return obj.sender

    template = "djangoobjfeed/render_tweet_entry.%(format)s"

class BlogFeedEntry(ObjFeedEntry):
    obj = django.db.models.ForeignKey(pinax.apps.blog.models.Post, related_name='feed_entry')

    @classmethod
    def get_author_from_obj(cls, obj):
        return obj.author

    template = "djangoobjfeed/render_blog_entry.%(format)s"

class ImageFeedEntry(ObjFeedEntry):
    obj = django.db.models.ForeignKey(pinax.apps.photos.models.Image, related_name='feed_entry')

    @classmethod
    def get_author_from_obj(cls, obj):
        return obj.member

    template = "djangoobjfeed/render_photo_entry.%(format)s"

