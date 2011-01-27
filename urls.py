from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^post/?$', 'djangoobjfeed.views.post'),
    (r'^post-comment/?$', 'djangoobjfeed.views.post_comment'),
    (r'^update-comment/?$', 'djangoobjfeed.views.update_comment'),
    (r'^delete-comment/?$', 'djangoobjfeed.views.delete_comment'),
    (r'^feed/user/(?P<username>[^/]+)/?$', 'djangoobjfeed.views.get_objfeed_for_user'),
    (r'^feed/(?P<objfeed_id>[^/]+)/?$', 'djangoobjfeed.views.get_objfeed'),
    (r'^feed-entry/(?P<feed_entry_id>[^/]+)/?$', 'djangoobjfeed.views.get_feed_entry'),
)
