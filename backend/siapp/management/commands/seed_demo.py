"""Seed local demo data for the Salesforce-notes-on-map feature.

Recreates everything needed to run the feature on a fresh machine (the SQLite dev
DB is gitignored, so a new clone starts empty):
  - a customer, product chain, and buyers across Germany + USA with plant locations
  - each buyer's `salesforce_account_id` link to a Salesforce sample account
  - a `mapuser` login (Managers group + customer -> can load the map) and an `admin` superuser

Idempotent: safe to run repeatedly. Run with the dev env:
    ENV=DEV_LOCAL python manage.py migrate
    python manage.py seed_demo

NOTE: This only seeds the local DB. The Salesforce notes themselves live in the
shared cloud org and are reached via SF_* credentials in backend/.env (not seeded here).
The mapuser/admin passwords below are LOCAL DEMO credentials only.
"""
from datetime import date

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from siapp.models import (
    Buyer, BuyerPlants, Continent, Country, Customer, CustomerPeriod,
    GeoCoordinates, Industry, ItemsToCustomerPeriods, Product, ProductCluster,
    ProductDescription, ProductGroup, Region, TrademarkGroup, User, Year,
)

# (buyer name, salesforce_account_id or None, country, city, lat, lng) — note counts in
# the shared org: Edge 5, Burlington 3, Pyramid 2, Dickenson 1, Grand Hotels 0, Mueller none.
BUYERS = [
    ("Edge Communications",      "001g500000NHU7mAAH", "Germany",       "Berlin",      52.52,  13.40),
    ("Burlington Textiles Corp", "001g500000NHU7nAAH", "Germany",       "Munich",      48.137, 11.575),
    ("Pyramid Construction",     "001g500000NHU7oAAH", "Germany",       "Frankfurt",   50.11,   8.68),
    ("Mueller Logistik GmbH",    None,                 "Germany",       "Hamburg",     53.55,   9.99),
    ("Grand Hotels & Resorts",   "001g500000NHU7qAAH", "United States", "New York",    40.71, -74.01),
    ("Dickenson plc",            "001g500000NHU7pAAH", "United States", "Los Angeles", 34.05, -118.24),
]

MAP_USER = ("mapuser", "mapuser@demo.local", "MapTest1234!")   # local demo only
ADMIN_USER = ("admin", "admin@demo.local", "Admin@12345")       # local demo only


class Command(BaseCommand):
    help = "Seed local demo data (buyers, Salesforce links, and login users) for the map feature."

    @transaction.atomic
    def handle(self, *args, **options):
        europe, _ = Continent.objects.get_or_create(continent_name="Europe")
        w_europe, _ = Region.objects.get_or_create(region_name="Western Europe")
        germany, _ = Country.objects.get_or_create(
            country_name="Germany",
            defaults={"continent": europe, "region": w_europe, "country_code": "de"},
        )
        n_america, _ = Continent.objects.get_or_create(continent_name="North America")
        na_region, _ = Region.objects.get_or_create(region_name="North America")
        usa, _ = Country.objects.get_or_create(
            country_name="United States",
            defaults={"continent": n_america, "region": na_region, "country_code": "us"},
        )
        countries = {"Germany": germany, "United States": usa}

        industry, _ = Industry.objects.get_or_create(industry_name="Automotive")
        cluster, _ = ProductCluster.objects.get_or_create(
            product_cluster_name="Electronics", defaults={"industry": industry})
        group, _ = ProductGroup.objects.get_or_create(
            product_group_name="Sensors", defaults={"product_cluster": cluster})
        product, _ = Product.objects.get_or_create(
            product_name="Pressure Sensor", defaults={"product_group": group})
        trademark, _ = TrademarkGroup.objects.get_or_create(trademark_group_name="TG-Demo")
        description, _ = ProductDescription.objects.get_or_create(
            product_description_name="PD-Demo",
            defaults={"product": product, "trademark_group": trademark})

        customer, _ = Customer.objects.get_or_create(customer_name="Demo Customer")
        year, _ = Year.objects.get_or_create(year=2025)
        period, _ = CustomerPeriod.objects.get_or_create(
            customer=customer, name="2025",
            defaults={"begin": date(2025, 1, 1), "end": date(2025, 12, 31), "year": year})

        for name, sf_id, country_name, city, lat, lng in BUYERS:
            country = countries[country_name]
            buyer, _ = Buyer.objects.get_or_create(buyer_name=name)
            buyer.salesforce_account_id = sf_id
            buyer.save()

            addr, _ = GeoCoordinates.objects.get_or_create(
                city=city, country=country,
                defaults={"lat": lat, "lng": lng, "capital": False, "state": city})
            plant, _ = BuyerPlants.objects.get_or_create(
                buyer_plant_name=f"{name} Plant", buyer=buyer, city=addr)
            ItemsToCustomerPeriods.objects.get_or_create(
                buyer=buyer, customerperiod=period, product=product,
                country_buyer=country, address_buyer=addr,
                defaults={
                    "product_cluster": cluster, "product_group": group,
                    "product_description": description, "buyer_plant": plant,
                    "spend": 50000, "quantity": 250,
                    "address_customer": addr, "country_customer": country,
                })

        managers, _ = Group.objects.get_or_create(name="Managers")
        for username, email, password in (MAP_USER, ADMIN_USER):
            user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            if username == MAP_USER[0]:
                user.customer = customer
            user.save()
            if username == MAP_USER[0]:
                user.groups.add(managers)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write(f"  app login:   {MAP_USER[0]} / {MAP_USER[2]}  (map: Electronics > Sensors > Pressure Sensor)")
        self.stdout.write(f"  admin login: {ADMIN_USER[0]} / {ADMIN_USER[2]}  (/admin/)")
        self.stdout.write(f"  buyers: {Buyer.objects.count()} | Germany + United States")
