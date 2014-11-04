# -*- coding: utf-8 -*-
from django.conf.urls import *

urlpatterns = patterns('',
    (r'^feed/user/(?P<username>[^/]+)/?$', 'appomatic_djangoobjfeed.views.get_objfeed_for_user'),
    (r'^feed/named/(?P<name>[^/]+)/?$', 'appomatic_djangoobjfeed.views.get_objfeed_for_name'),
    (r'^feed/(?P<objfeed_id>[^/]+)/?$', 'appomatic_djangoobjfeed.views.get_objfeed'),
    (r'^feed-entry/(?P<feed_entry_id>[^/]+)/?$', 'appomatic_djangoobjfeed.views.get_feed_entry'),
    (r'^avatar/', include('avatar.urls')),
)
