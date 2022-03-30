from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def limit_str(string, num: int):
    i = 0
    lim_string = ''
    for char in string:
        i += 1
        if i <= num:
            lim_string += char
    return lim_string
