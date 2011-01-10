import django.db.models
import django.contrib.auth.models
import pinax.apps.tribes.models
import microblogging.models
import pinax.apps.blog.models
import fcdjangoutils.modelhelpers
import django.template
import django.template.loader
import datetime

# Feeds

class ObjFeed(django.db.models.Model, fcdjangoutils.modelhelpers.SubclasModelMixin):
    class __metaclass__(django.db.models.Model.__metaclass__):
        def __init__(cls, *arg, **kw):
            django.db.models.Model.__metaclass__.__init__(cls, *arg, **kw)
            if cls.__name__ != 'ObjFeed':
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

    def __unicode__(self):
        return "Feed for %s" % (self.owner,)

    @property
    def entries(self):
        return self.all_entries.filter(obj_feed_entry__posted_at__lte = datetime.datetime.now())


class UserFeed(ObjFeed):
    owner = django.db.models.OneToOneField(django.contrib.auth.models.User, primary_key=True, related_name="feed")

class TribeFeed(ObjFeed):
    owner = django.db.models.OneToOneField(pinax.apps.tribes.models.Tribe, primary_key=True, related_name="feed")


# Subscriptions

class ObjFeedSubscription(django.db.models.Model):
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

class FeedEntry(django.db.models.Model, fcdjangoutils.modelhelpers.SubclasModelMixin):
    objects = FeedEntryManager()
    feed = django.db.models.ForeignKey("ObjFeed", related_name="all_entries")
    obj_feed_entry = django.db.models.ForeignKey("ObjFeedEntry", related_name="feed_entry")

    @property
    def display_name(self):
        return self.obj_feed_entry.subclassobject.display_name

    def render(self, format = 'html', context = None):
        ctx = django.template.Context({})
        ctx['csrf_token'] = context['csrf_token']
        ctx['feed_entry'] = self
        return django.template.loader.get_template(self.obj_feed_entry.template % {'format':format}
                                                   ).render(ctx)

    # Very very spartan so it can't break into infinite recursion hell... I.e. DONT't call templates here!!!
    def __repr__(self):
        return "%s: %s posted to %s" % (type(self), self.obj_feed_entry.author, self.feed)

    def __unicode__(self):
        return "%s posted to %s" % (self.render('txt'), self.feed)

class CommentFeedEntryManager(django.db.models.Manager):
    def get_query_set(self):
        return django.db.models.Manager.get_query_set(self).order_by("posted_at")

class CommentFeedEntry(django.db.models.Model, fcdjangoutils.modelhelpers.SubclasModelMixin):
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
        ctx = django.template.Context({})
        if context: ctx['csrf_token'] = context['csrf_token']
        class Dummy(object):
            pass
        ctx['feed_entry'] = Dummy()
        ctx['feed_entry'].obj_feed_entry = self
        return django.template.loader.get_template(self.template % {'format':format}
                                                   ).render(ctx)

# Feed entry adaptors for objects

class ObjFeedEntry(django.db.models.Model, fcdjangoutils.modelhelpers.SubclasModelMixin):
    class __metaclass__(django.db.models.Model.__metaclass__):
        def __init__(cls, *arg, **kw):
            django.db.models.Model.__metaclass__.__init__(cls, *arg, **kw)
            if cls.__name__ != 'ObjFeedEntry':
                django.db.models.signals.post_save.connect(cls.obj_post_save, sender=cls.obj.field.rel.to)

    @fcdjangoutils.modelhelpers.subclassproxy
    @property
    def obj(self): raise fcdjangoutils.modelhelpers.MustBeOverriddenError
    posted_at = django.db.models.DateTimeField(auto_now=True)
    author = django.db.models.ForeignKey(django.contrib.auth.models.User, related_name="feed_postings")

    @classmethod
    def get_author_from_obj(cls, instance):
        raise NotImplementedError

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
        if hasattr(author, 'friends'):
            for friend in author.friends.all():
                if hasattr(friend, 'feed'):
                    yield lambda feed_entry: True, friend.feed

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
        for matches_subscription, feed in cls.copy_feeds(instance, author):
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


# Feed entry adapers

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
