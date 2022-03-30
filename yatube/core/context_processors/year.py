import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    value = dt.datetime.now()

    return {'year': value.strftime('%Y')}
