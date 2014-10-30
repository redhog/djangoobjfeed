import django.template
from fcdjangoutils.timer import Timer 

register = django.template.Library()

@register.tag
def objfeed(feed, only_own = False):
    feed = feed.subclassobject
    return feed.render(style="inline.html", context_arg={"only_own": only_own});

@register.tag
def objfeed_for_obj(obj, only_own = False):
    feed = obj.feed.subclassobject
    return feed.render(style="inline.html", context_arg={"only_own": only_own});

class RenderNode(django.template.Node):
    def __init__(self, **kw):
        self.vars = {
            key: django.template.Variable(value)
            for key, value in kw.iteritems()
            }

    def render(self, context):
        vars = {
            key: value.resolve(context)
            for key, value in
            self.vars.iteritems()
            }
        obj = vars.pop("obj")
        args = {'context_arg': vars}
        if 'style' in vars: args['style'] = vars.pop("style")
        return obj.render(**args)

@register.tag
def render(parser, token):
    tokens = dict(item.split("=", 1)
                  for item in token.split_contents()[1:])
    return RenderNode(**tokens)

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
