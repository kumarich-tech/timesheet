from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
@register.filter
def filter_for(services, is_fixed_salary):
    return services.filter(for_salary_based=is_fixed_salary)
@register.filter
def get_day_label(day):
    import calendar
    # Пн - 0, Вс - 6
    week_day = calendar.weekday(2024, 1, int(day))  # Заглушка: год и месяц нужно будет передавать
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    return days[week_day]
