import django.http
import django.shortcuts
import djangoobjfeed.models

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
        subject = request.POST['subject'],
        content = request.POST['content']
        ).save()

    return django.shortcuts.redirect(request.META['HTTP_REFERER'])
