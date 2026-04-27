from django.http import HttpRequest, JsonResponse
from ninja import Query, Router
from ninja_jwt.authentication import JWTAuth

from siapp.models import is_employee_or_above, user_has_product_access
from siapp.views.buyer_view.infotexts import buyer_map_infotext
from siapp.views.buyer_view.schema import BuyerBuyerMapRequest
from siapp.views.buyer_view.views_buyer import calculate_buyer_buyer_map
from siapp.views.views_common import get_date_range

router_buyer = Router()


@router_buyer.get("/buyer_map/", auth=JWTAuth())
def buyer_buyer_map(request: HttpRequest, parameters: BuyerBuyerMapRequest = Query(...)) -> dict:
    if not is_employee_or_above(request.user):
        return JsonResponse({'error': 'User does not have permission to access this page.'}, status=403)

    selected_product_ids = list(map(int, parameters.product_id.split(",")))
    if not user_has_product_access(request.user, selected_product_ids):
        return JsonResponse({'error': 'Access to one or more requested products is not permitted.'}, status=403)

    country_ids = list(map(int, parameters.country_id.split(",")))

    customer_id: int = request.user.customer_id
    selected_start_date, selected_end_date = get_date_range()
    result = calculate_buyer_buyer_map(customer_id, selected_end_date, selected_start_date, selected_product_ids, country_ids)
    result["infotext"] = buyer_map_infotext("de")

    return result
