from django import template

register = template.Library()

@register.filter
def field_col(field):
    name = field.name.lower()
    # Assign field width based on name
    if "name" in name:
        return 3
    elif "contact" in name:
        return 2
    elif "contribution" in name:
        return 2
    else:
        return 2
