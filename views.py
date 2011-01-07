import django.http
import django.shortcuts
import djangoobjfeed.models
import django.contrib.auth.models

def post_comment(request, *arg, **kw):    
    comment_on_feed_entry = None
    comment_on_comment = None

    if 'comment_on_feed_entry' in request.POST:
        comment_on_feed_entry = djangoobjfeed.models.ObjFeedEntry.objects.get(id=int(request.POST['comment_on_feed_entry']))

    if 'comment_on_comment' in request.POST:
        comment_on_comment = djangoobjfeed.models.CommentFeedEntry.objects.get(id=int(request.POST['comment_on_comment']))

    djangoobjfeed.models.CommentFeedEntry(
        author = request.user,
        comment_on_feed_entry = comment_on_feed_entry,
        comment_on_comment = comment_on_comment,
        content = request.POST['content']
        ).save()

    return django.shortcuts.redirect(request.META['HTTP_REFERER'])

def get_objfeed(request, objfeed_id):
    data = {}
    feed = djangoobjfeed.models.ObjFeed.objects.get(id=objfeed_id)
    data["entries"] = feed.entries.order_by("-obj_feed_entry__posted_at").all()[:5]
    return django.shortcuts.render_to_response(
        'djangoobjfeed/objfeed.html', 
        data,
        context_instance=django.template.RequestContext(request))

def get_objfeed_for_user(request, username):
    usr = django.contrib.auth.models.User.objects.get(username=username)
    return get_objfeed(request, usr.feed.id)
