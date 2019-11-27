from django import template
import locale

register = template.Library()


@register.filter()
def currency(value):
    if value == None:
        return
    return locale.currency(value, grouping=True)