# -*- coding: utf-8 -*-
import django.contrib.admin
import djangoobjfeed.models

django.contrib.admin.site.register(djangoobjfeed.models.UserFeed)
django.contrib.admin.site.register(djangoobjfeed.models.TribeFeed)
django.contrib.admin.site.register(djangoobjfeed.models.UserFeedSubscription)
django.contrib.admin.site.register(djangoobjfeed.models.ObjFeedEntry)
django.contrib.admin.site.register(djangoobjfeed.models.CommentFeedEntry)
django.contrib.admin.site.register(djangoobjfeed.models.TweetFeedEntry)
django.contrib.admin.site.register(djangoobjfeed.models.BlogFeedEntry)

