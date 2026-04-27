from django.http import HttpRequest, JsonResponse
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from siapp.models import is_employee_or_above, ItemsToCustomerPeriods
from siapp.views.views_common import get_date_range, get_current_periods

router_lists = Router()


def _parse_ids(raw: str) -> list[int]:
    if not raw or not raw.strip():
        return []
    return [int(x) for x in raw.split(",") if x.strip()]


@router_lists.get("/buyermap/cluster/", auth=JWTAuth())
def get_buyermap_clusters(request: HttpRequest) -> list:
    if not is_employee_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    customer_id = request.user.customer_id
    selected_start_date, selected_end_date = get_date_range()
    period_ids = get_current_periods(customer_id, selected_start_date, selected_end_date)

    allowed_cluster_ids = list(
        request.user.allowed_product_clusters.values_list("id", flat=True)
    )

    qs = ItemsToCustomerPeriods.objects.filter(customerperiod_id__in=period_ids)
    if allowed_cluster_ids:
        qs = qs.filter(product_cluster_id__in=allowed_cluster_ids)

    rows = qs.values_list(
        "product_cluster_id", "product_cluster__product_cluster_name"
    ).distinct()

    result = [
        {"product_cluster_id": cid, "product_cluster_name": name}
        for cid, name in rows
        if name
    ]
    result.sort(key=lambda x: x["product_cluster_name"])
    return result


@router_lists.get("/buyermap/group/", auth=JWTAuth())
def get_buyermap_groups(request: HttpRequest, cluster_id: str) -> list:
    if not is_employee_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    customer_id = request.user.customer_id
    selected_start_date, selected_end_date = get_date_range()
    period_ids = get_current_periods(customer_id, selected_start_date, selected_end_date)
    cluster_ids = _parse_ids(cluster_id)

    qs = ItemsToCustomerPeriods.objects.filter(customerperiod_id__in=period_ids)
    if cluster_ids:
        qs = qs.filter(product_cluster_id__in=cluster_ids)

    rows = qs.values_list(
        "product_group_id", "product_group__product_group_name"
    ).distinct()

    result = [
        {"product_group_id": gid, "product_group_name": name}
        for gid, name in rows
        if name
    ]
    result.sort(key=lambda x: x["product_group_name"])
    return result


@router_lists.get("/buyermap/product/", auth=JWTAuth())
def get_buyermap_products(request: HttpRequest, group_id: str) -> list:
    if not is_employee_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    customer_id = request.user.customer_id
    selected_start_date, selected_end_date = get_date_range()
    period_ids = get_current_periods(customer_id, selected_start_date, selected_end_date)
    group_ids = _parse_ids(group_id)

    qs = ItemsToCustomerPeriods.objects.filter(customerperiod_id__in=period_ids)
    if group_ids:
        qs = qs.filter(product_group_id__in=group_ids)

    rows = qs.values_list(
        "product_id", "product__product_name"
    ).distinct()

    result = [
        {"product_id": pid, "product_name": name}
        for pid, name in rows
        if name
    ]
    result.sort(key=lambda x: x["product_name"])
    return result


@router_lists.get("/buyermap/country/", auth=JWTAuth())
def get_buyermap_countries(request: HttpRequest, product_id: str) -> list:
    if not is_employee_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    customer_id = request.user.customer_id
    selected_start_date, selected_end_date = get_date_range()
    period_ids = get_current_periods(customer_id, selected_start_date, selected_end_date)
    product_ids = _parse_ids(product_id)

    qs = ItemsToCustomerPeriods.objects.filter(customerperiod_id__in=period_ids)
    if product_ids:
        qs = qs.filter(product_id__in=product_ids)

    rows = qs.values_list(
        "country_buyer_id",
        "country_buyer__country_name",
        "country_buyer__country_code",
    ).distinct()

    result = [
        {"country_id": cid, "country_name": name, "country_code": code}
        for cid, name, code in rows
        if name
    ]
    result.sort(key=lambda x: x["country_name"])
    return result
