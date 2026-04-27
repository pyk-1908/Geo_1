from collections import defaultdict
from datetime import datetime
import random
from django.db.models import Count

from siapp.models import CustomerPeriod, ItemsToCustomerPeriods, Customer, Country, CustomerPlants


def calculate_buyer_buyer_map(customer_id: int, selected_end_date: str, selected_start_date: str, selected_product_ids: list[int], country_ids: list[int]) -> dict:

    map_country_dict = {"country": []}

    selected_start_date = datetime.strptime(selected_start_date, "%Y-%m-%d")
    selected_end_date = datetime.strptime(selected_end_date, "%Y-%m-%d")

    current_periods: list[int] = list(
        CustomerPeriod.objects.filter(
            customer_id=customer_id,
            begin__lte=selected_end_date,
            end__gte=selected_start_date,
        ).values_list("id", flat=True)
    )

    icps_period_actual = ItemsToCustomerPeriods.objects.filter(
        customerperiod_id__in=current_periods,
        product_id__in=selected_product_ids,
        country_buyer_id__in=country_ids,
    )
    num_buyer_plants = (
        icps_period_actual
        .values("country_buyer_id", "buyer_id")
        .annotate(distinct_addresses=Count("address_buyer_id", distinct=True))
    )

    num_buyer_plants_dict: dict[int, dict[int, int]] = {}
    for entry in num_buyer_plants:
        b_id = entry["buyer_id"]
        c_id = entry["country_buyer_id"]
        num_buyer_plants_dict.setdefault(b_id, {})[c_id] = entry["distinct_addresses"]

    customers_map = Customer.objects.in_bulk()
    countries_map = Country.objects.in_bulk()

    for country_id in country_ids:
        country_obj = countries_map.get(country_id)
        if not country_obj:
            continue

        buyer_plants_dict: dict[tuple, list] = defaultdict(list)
        for element in ItemsToCustomerPeriods.objects.filter(
            customerperiod_id__in=current_periods,
            product_id__in=selected_product_ids,
            country_buyer_id=country_id,
        ).values(
            "buyer_id",
            "buyer__buyer_name",
            "address_buyer_id",
            "address_buyer__city",
            "address_buyer__state",
            "address_buyer__lat",
            "address_buyer__lng",
        ).distinct():
            buyer_key = (element["buyer_id"], element["buyer__buyer_name"])
            buyer_plants_dict[buyer_key].append({
                "city_name": element["address_buyer__city"],
                "city_id": element["address_buyer_id"],
                "lat": element["address_buyer__lat"],
                "lng": element["address_buyer__lng"],
                "state_name": element["address_buyer__state"],
            })

        result = []
        for (buyer_id, buyer_name) in buyer_plants_dict:
            locations = list(
                {loc["city_id"]: loc for loc in buyer_plants_dict[(buyer_id, buyer_name)]}.values()
            )
            result.append({
                "buyer_name": buyer_name,
                "buyer_id": buyer_id,
                "growth_score": random.randint(0, 100),
                "num_plants_abs": num_buyer_plants_dict.get(buyer_id, {}).get(country_id, 0),
                "locations": locations,
            })

        customer_plants_qs = CustomerPlants.objects.filter(
            customer_id=customer_id,
            city__country_id=country_id,
        ).values(
            "customer_id",
            "city_id",
            "city__city",
            "city__state",
            "city__lat",
            "city__lng",
        )

        customer_plants_dict: dict[int, list] = {}
        for cp in customer_plants_qs:
            cid = cp["customer_id"]
            customer_plants_dict.setdefault(cid, []).append({
                "city_name": cp["city__city"],
                "city_id": cp["city_id"],
                "lat": cp["city__lat"],
                "lng": cp["city__lng"],
                "state_name": cp["city__state"],
            })

        seller_locations = customer_plants_dict.get(customer_id, [])
        unique_seller_locations = list(
            {loc["city_id"]: loc for loc in seller_locations}.values()
        )

        customer_obj = customers_map.get(customer_id)
        map_country_dict["country"].append({
            "country_name": country_obj.country_name,
            "country_id": country_id,
            "country_code": country_obj.country_code,
            "buyers": result,
            "seller": {
                "seller_name": customer_obj.customer_name if customer_obj else "",
                "seller_id": customer_id,
                "locations": unique_seller_locations,
            },
        })

    return map_country_dict
