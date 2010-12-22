import django.template

register = django.template.Library()

@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed_for_user(context, user, is_me):
    return {"entries": user.feed.entries.order_by("-posted_at").all()[:5], 'STATIC_URL': context['STATIC_URL']}

@register.inclusion_tag("djangoobjfeed/objfeed.html", takes_context=True)
def objfeed_for_tribe(context, tribe):
    return {"entries": tribe.feed.entries.order_by("-posted_at").all()[:5], 'STATIC_URL': context['STATIC_URL']}

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
