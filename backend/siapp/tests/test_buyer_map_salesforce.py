"""Verifies the buyer map exposes a buyer's salesforce_account_id (used by the
frontend to fetch that buyer's Salesforce notes for the map popup)."""
from datetime import date

from django.test import TestCase

from siapp.models import (
    Buyer, BuyerPlants, Continent, Country, Customer, CustomerPeriod,
    GeoCoordinates, Industry, ItemsToCustomerPeriods, Product, ProductCluster,
    ProductDescription, ProductGroup, Region, TrademarkGroup, Year,
)
from siapp.views.buyer_view.views_buyer import calculate_buyer_buyer_map

SF_ACCOUNT_ID = "001g500000NHU7mAAH"


class BuyerMapSalesforceTest(TestCase):
    def setUp(self):
        continent = Continent.objects.create(continent_name="Europe")
        region = Region.objects.create(region_name="Western Europe")
        self.country = Country.objects.create(
            country_name="Germany", continent=continent, region=region, country_code="de",
        )
        industry = Industry.objects.create(industry_name="Automotive")
        cluster = ProductCluster.objects.create(product_cluster_name="PC", industry=industry)
        group = ProductGroup.objects.create(product_group_name="PG", product_cluster=cluster)
        self.product = Product.objects.create(product_name="P", product_group=group)
        trademark = TrademarkGroup.objects.create(trademark_group_name="TG")
        description = ProductDescription.objects.create(
            product_description_name="PD", product=self.product, trademark_group=trademark,
        )

        self.customer = Customer.objects.create(customer_name="MyCo")
        year = Year.objects.create(year=2025)
        period = CustomerPeriod.objects.create(
            customer=self.customer, begin=date(2025, 1, 1), end=date(2025, 12, 31),
            name="2025", year=year,
        )

        self.buyer = Buyer.objects.create(
            buyer_name="Edge Communications", salesforce_account_id=SF_ACCOUNT_ID,
        )
        addr = GeoCoordinates.objects.create(
            country=self.country, city="Berlin", lat=52.52, lng=13.40, capital=True, state="BE",
        )
        buyer_plant = BuyerPlants.objects.create(
            buyer_plant_name="Edge Plant", buyer=self.buyer, city=addr,
        )

        ItemsToCustomerPeriods.objects.create(
            product_cluster=cluster, product_group=group, product=self.product,
            product_description=description, buyer=self.buyer, buyer_plant=buyer_plant,
            customerperiod=period, spend=1000, quantity=10,
            address_buyer=addr, country_buyer=self.country,
            address_customer=addr, country_customer=self.country,
        )

    def test_buyer_map_includes_salesforce_account_id(self):
        result = calculate_buyer_buyer_map(
            self.customer.id, "2025-12-31", "2025-01-01", [self.product.id], [self.country.id],
        )

        buyers = result["country"][0]["buyers"]
        edge = next(b for b in buyers if b["buyer_name"] == "Edge Communications")
        self.assertEqual(edge["salesforce_account_id"], SF_ACCOUNT_ID)

    def test_buyer_without_salesforce_id_returns_none(self):
        self.buyer.salesforce_account_id = None
        self.buyer.save()

        result = calculate_buyer_buyer_map(
            self.customer.id, "2025-12-31", "2025-01-01", [self.product.id], [self.country.id],
        )

        edge = next(b for b in result["country"][0]["buyers"] if b["buyer_name"] == "Edge Communications")
        self.assertIsNone(edge["salesforce_account_id"])
