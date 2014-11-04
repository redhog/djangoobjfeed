# -*- coding: utf-8 -*-
import django.http
import django.shortcuts
import django.contrib.auth.models
from fcdjangoutils.timer import Timer 
import appomatic_djangoobjfeed.models

def get_return_address(request):
    if '_next' in request.POST:
        return request.POST['_next']
    if '_next' in request.GET:
        return request.GET['_next']
    if 'HTTP_REFERER' in request.META:
        return request.META['HTTP_REFERER']
    return '/'


def get_feed_entry(request, feed_entry_id):
    entry = appomatic_djangoobjfeed.models.FeedEntry.objects.get(id=int(feed_entry_id))
    return entry.render(style="page.html", as_response=True)

def get_objfeed(request, objfeed_id):
    data = {}
    feed = appomatic_djangoobjfeed.models.ObjFeed.objects.get(id=objfeed_id)
    data["feed"] = feed
    data["allowed_to_post"] = feed.subclassobject.allowed_to_post(request.user)
    data["entries"] = feed.entries.order_by("-obj_feed_entry__posted_at").all()[:10]
    x = list(data["entries"])
    
    with Timer("Render"):
        return django.shortcuts.render_to_response(
            'djangoobjfeed/objfeed.html', 
            data,
            context_instance=django.template.RequestContext(request))


def get_objfeed_for_user(request, username):
    usr = django.contrib.auth.models.User.objects.get(username=username)
    return get_objfeed(request, usr.feed.id)

def get_objfeed_for_name(request, name):
    feed = appomatic_djangoobjfeed.models.NamedFeed.objects.get(name=name)
    return get_objfeed(request, feed.id)
