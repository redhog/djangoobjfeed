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
