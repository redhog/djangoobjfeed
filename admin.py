# -*- coding: utf-8 -*-
import django.contrib.admin
import djangoobjfeed.models

django.contrib.admin.site.register(djangoobjfeed.models.UserFeed)
django.contrib.admin.site.register(djangoobjfeed.models.NamedFeed)
django.contrib.admin.site.register(djangoobjfeed.models.TribeFeed)
django.contrib.admin.site.register(djangoobjfeed.models.UserFeedSubscription)

class ObjFeedEntryAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['author', 'posted_at', 'obj']
django.contrib.admin.site.register(djangoobjfeed.models.ObjFeedEntry, ObjFeedEntryAdmin)

class CommentFeedEntryAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['author', 'posted_at', 'comment_on_feed_entry', 'comment_on_comment']
django.contrib.admin.site.register(djangoobjfeed.models.CommentFeedEntry, CommentFeedEntryAdmin)

class MessageAdmin(django.contrib.admin.ModelAdmin):
    list_display_links = list_display = ['feed','author']
django.contrib.admin.site.register(djangoobjfeed.models.Message, MessageAdmin)

django.contrib.admin.site.register(djangoobjfeed.models.MessageFeedEntry, ObjFeedEntryAdmin)
django.contrib.admin.site.register(djangoobjfeed.models.TweetFeedEntry, ObjFeedEntryAdmin)
django.contrib.admin.site.register(djangoobjfeed.models.BlogFeedEntry, ObjFeedEntryAdmin)

