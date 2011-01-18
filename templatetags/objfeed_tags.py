import django.template

register = django.template.Library()

@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed_for_user(context, user, is_me):
    context["feed"] = user.feed
    context["allowed_to_post"] = user.feed.subclassobject.allowed_to_post(context['request'].user)
    context["entries"] = user.feed.entries.order_by("-obj_feed_entry__posted_at").all()[:5]
    return context

@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed_for_tribe(context, tribe):
    context["feed"] = tribe.feed
    context["allowed_to_post"] = tribe.feed.subclassobject.allowed_to_post(context['request'].user)
    context["entries"] = tribe.feed.entries.order_by("-obj_feed_entry__posted_at").all()[:5]
    return context



@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed(context, feed):
    context["feed"] = feed
    context["allowed_to_post"] = feed.subclassobject.allowed_to_post(context['request'].user)
    context["entries"] = feed.entries.order_by("-obj_feed_entry__posted_at").all()[:5]
    return context

@register.inclusion_tag("djangoobjfeed/comments.html", takes_context=True)
def objfeed_comments(context, obj_feed_entry):
    context["obj_feed_entry"] = obj_feed_entry
    return context



@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed_for_obj(context, obj):
    context["feed"] = obj.feed
    context["allowed_to_post"] = obj.feed.subclassobject.allowed_to_post(context['request'].user)
    context["entries"] = obj.feed.entries.order_by("-obj_feed_entry__posted_at").all()[:5]
    return context

@register.inclusion_tag("djangoobjfeed/comments.html", takes_context=True)
def objfeed_comments_for_obj(context, obj):
    context["obj_feed_entry"] = obj.feed_entry.all()[0]
    return context


class RenderNode(django.template.Node):
    def __init__(self, entry, format):
        self.entry = django.template.Variable(entry)
        self.format = django.template.Variable(format)

    def render(self, context):
        return self.entry.resolve(context).render(self.format.resolve(context), context)

@register.tag
def render(parser, token):
    try:
        tag_name, entry, format = token.split_contents()
    except ValueError:
        raise django.template.TemplateSyntaxError, "%r tag requires two arguments" % token.contents.split()[0]
    return RenderNode(entry, format)

@register.tag
def if_allowed_to_post_comment(parser, token):
    """Usage:
    {% if_allowed_to_post_comment obj_feed_entry user' %}
      Some HTML
    {% if_allowed_to_post_comment_end %}
"""
    try:
        tag_name, obj_feed_entry, user = token.split_contents()
    except ValueError:
        raise django.template.TemplateSyntaxError, "%r tag requires two argument" % token.contents.split()[0]

    nodelist_required = parser.parse(('if_allowed_to_post_comment_end',))
    parser.delete_first_token()
    
    obj_feed_entry = django.template.Variable(obj_feed_entry)
    user = django.template.Variable(user)
    
    class Node(django.template.Node):
        def render(self, context):
            obj_feed_entry_val = obj_feed_entry.resolve(context).subclassobject
            user_val = user.resolve(context)
            if obj_feed_entry_val.allowed_to_post_comment(user_val):
                return nodelist_required.render(context)
            else:
                return ""
    return Node()
