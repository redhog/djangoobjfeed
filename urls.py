from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^post/?', 'djangoobjfeed.views.post_comment'),
    (r'^feed/user/(?P<username>[^/]+)/?', 'djangoobjfeed.views.get_objfeed_for_user'),
    (r'^feed/(?P<objfeed_id>[^/]+)/?', 'djangoobjfeed.views.get_objfeed'),
)
