# -*- coding: utf-8 -*-
import django.contrib.admin
import appomatic_djangoobjfeed.models

django.contrib.admin.site.register(appomatic_djangoobjfeed.models.UserFeed)
django.contrib.admin.site.register(appomatic_djangoobjfeed.models.NamedFeed)
if (hasattr(appomatic_djangoobjfeed.models, 'TribeFeed')): django.contrib.admin.site.register(appomatic_djangoobjfeed.models.TribeFeed)
django.contrib.admin.site.register(appomatic_djangoobjfeed.models.UserFeedSubscription)

class ObjFeedEntryAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['author', 'posted_at', 'obj']
django.contrib.admin.site.register(appomatic_djangoobjfeed.models.ObjFeedEntry, ObjFeedEntryAdmin)

class CommentFeedEntryAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['author', 'posted_at', 'comment_on_feed_entry', 'comment_on_comment']
django.contrib.admin.site.register(appomatic_djangoobjfeed.models.CommentFeedEntry, CommentFeedEntryAdmin)

class MessageAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['feed','author']
django.contrib.admin.site.register(appomatic_djangoobjfeed.models.Message, MessageAdmin)

django.contrib.admin.site.register(appomatic_djangoobjfeed.models.MessageFeedEntry, ObjFeedEntryAdmin)
if (hasattr(appomatic_djangoobjfeed.models, 'TweetFeedEntry')): django.contrib.admin.site.register(appomatic_djangoobjfeed.models.TweetFeedEntry, ObjFeedEntryAdmin)
if (hasattr(appomatic_djangoobjfeed.models, 'BlogFeedEntry')): jango.contrib.admin.site.register(appomatic_djangoobjfeed.models.BlogFeedEntry, ObjFeedEntryAdmin)
if (hasattr(appomatic_djangoobjfeed.models, 'ImageFeedEntry')): jango.contrib.admin.site.register(appomatic_djangoobjfeed.models.ImageFeedEntry, ObjFeedEntryAdmin)
