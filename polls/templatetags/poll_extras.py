from django import template
import locale

register = template.Library()


@register.filter()
def currency(value):
    return locale.currency(value, grouping=True)