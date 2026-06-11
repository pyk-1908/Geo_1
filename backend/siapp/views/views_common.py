import gettext as gettext
from datetime import date

from dateutil.relativedelta import relativedelta

from siapp.models import ItemsToCustomerPeriods, CustomerPeriod

de = gettext.translation('messages', localedir='./siapp/views/Infotexts', languages=['de'])
en = gettext.translation('messages', localedir='./siapp/views/Infotexts', languages=['en'])


def set_language(language_code: str) -> None:
    if language_code == 'de':
        de.install()
    elif language_code == 'en':
        en.install()
    else:
        print("Sprache nicht unterstützt!")




def get_date_range() -> tuple[str, str]:
    begin_date = (
        ItemsToCustomerPeriods.objects
        .order_by("-customerperiod_id")
        .values_list("customerperiod__begin", flat=True)
        .first()
    )
    if begin_date is None:
        begin_date = date.today()

    selected_start_date = (begin_date - relativedelta(years=1)).strftime("%Y-%m-%d")
    selected_end_date = begin_date.strftime("%Y-%m-%d")
    return selected_start_date, selected_end_date


def get_current_periods(customer_id: int, selected_start_date: str, selected_end_date: str) -> list[int]:
    return list(
        CustomerPeriod.objects.filter(
            customer_id=customer_id,
            begin__lte=selected_end_date,
            end__gte=selected_start_date,
        ).values_list("id", flat=True)
    )
