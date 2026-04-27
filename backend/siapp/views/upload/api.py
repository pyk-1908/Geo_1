import logging
import os
import time
from io import StringIO

import numpy as np
import pandas as pd
import psycopg2
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q, QuerySet
from django.http import HttpRequest, JsonResponse
from ninja import File, Router
from ninja.files import UploadedFile
from ninja_jwt.authentication import JWTAuth
from pandas import DataFrame

from siapp.redis_cache import RedisCache

redis_cache = RedisCache(redis_url=os.getenv('REDIS_URL', 'redis://localhost'))

from siapp.models import (
    Buyer,
    BuyerPlants,
    Continent,
    Country,
    Customer,
    CustomerPeriod,
    CustomerPlants,
    GeoCoordinates,
    Industry,
    ItemsToCustomerPeriods,
    Product,
    ProductCluster,
    ProductDescription,
    ProductGroup,
    Region,
    RegionValues,
    TrademarkGroup,
    Year,
    is_manager_or_above,
)

logger = logging.getLogger("django")

router_upload = Router()


def log_default_value_to_excel(
    entity_type: str,
    default_values: str,
    country_name: str = None,
    city_name: str = None,
    subcategory_name: str = None,
    category_name: str = None,
    supplier_name: str = None,
    file_path="./logs/default_log.xlsx",
):
    log_entry = {
        'Model Table': entity_type,
        'Country': country_name,
        'City': city_name,
        'Category': category_name,
        'Subcategory': subcategory_name,
        'Supplier': supplier_name,
        'Default Values': default_values,
    }
    df = pd.DataFrame([log_entry])
    if not os.path.isfile(file_path):
        df.to_excel(file_path, index=False, engine='openpyxl')
    else:
        existing_df = pd.read_excel(file_path, engine='openpyxl')
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_excel(file_path, index=False, engine='openpyxl')


def reset_sequence(table_name: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                false
            );
        """)


@transaction.atomic
def process_db_sync(dfs: dict) -> None:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'siapp_user'
              AND constraint_type = 'FOREIGN KEY';
        """)
        fk_constraints = [row[0] for row in cursor.fetchall()]
        for fk in fk_constraints:
            cursor.execute(f"ALTER TABLE siapp_user DROP CONSTRAINT {fk};")

        tables = [
            'siapp_itemstocustomerperiods',
            'siapp_customer', 'siapp_buyerplants', 'siapp_customerplants',
            'siapp_productdescription', 'siapp_product', 'siapp_country',
            'siapp_continent', 'siapp_productgroup', 'siapp_geocoordinates',
            'siapp_productcluster', 'siapp_buyer', 'siapp_industry',
            'siapp_customerperiod', 'siapp_year', 'siapp_region',
            'siapp_regionvalues', 'siapp_trademarkgroup',
        ]
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")

    for _t in [
        'siapp_buyer', 'siapp_country', 'siapp_continent',
        'siapp_customer', 'siapp_geocoordinates', 'siapp_industry',
        'siapp_customerperiod', 'siapp_year', 'siapp_region',
        'siapp_productdescription', 'siapp_product', 'siapp_productcluster',
        'siapp_productgroup', 'siapp_regionvalues',
        'siapp_buyerplants', 'siapp_customerplants', 'siapp_trademarkgroup',
        'siapp_itemstocustomerperiods',
    ]:
        reset_sequence(_t)

    batch_size = 50000

    for key, df in dfs.items():
        dfs[key] = df.replace({np.nan: None})

    year = [Year(**row) for row in dfs["year"].to_dict(orient="records")]
    created_years = Year.objects.bulk_create(year)
    year_map = {uc.year: uc.id for uc in created_years}

    industry = [
        Industry(**{k: v for k, v in row.items() if k != "section"})
        for row in dfs["industry"].to_dict(orient="records")
    ]
    created_industry = Industry.objects.bulk_create(industry)
    industry_map = {uc.industry_name: uc.id for uc in created_industry}

    continents = [Continent(**row) for row in dfs["continent"].to_dict(orient="records")]
    created_continents = Continent.objects.bulk_create(continents)
    continents_map = {c.continent_name: c.id for c in created_continents}

    regions = [Region(**row) for row in dfs["region"].to_dict(orient="records")]
    created_region = Region.objects.bulk_create(regions)
    region_map = {c.region_name: c.id for c in created_region}

    countries = [
        Country(**{
            **row,
            "continent_id": continents_map[row["continent_id"]],
            "region_id": region_map[row["region_id"]],
            "country_code": row.get("country_code") or "NA",
        })
        for row in dfs["country"].to_dict(orient="records")
    ]
    created_countries = Country.objects.bulk_create(countries)
    country_map = {c.country_name: c.id for c in created_countries}

    region_values = [
        RegionValues(**{
            **row,
            "region_id": region_map[row["region_id"]],
            "industry_id": industry_map[row["industry_id"]],
        })
        for row in dfs["region_values"].to_dict(orient="records")
    ]
    RegionValues.objects.bulk_create(region_values)

    geo_coordinates = [
        GeoCoordinates(**{**row, "country_id": country_map[row["country_id"]]})
        for row in dfs["geocoordinates"].to_dict(orient="records")
    ]
    created_geo_coordinates = GeoCoordinates.objects.bulk_create(geo_coordinates)
    city_map = {geo.city: geo.id for geo in created_geo_coordinates}

    customers = [
        Customer(**{
            "customer_name": row["customer_name"],
            "headquarter_country_id": country_map[row["headquarter_country_id"]] if row.get("headquarter_country_id") else None,
            "headquarter_address_id": city_map[row["headquarter_address_id"]] if row.get("headquarter_address_id") else None,
        })
        for row in dfs["customer"].to_dict(orient="records")
    ]
    created_customers = Customer.objects.bulk_create(customers)
    customer_map = {c.customer_name: c.id for c in created_customers}

    product_cluster = [
        ProductCluster(**{
            "product_cluster_name": row["product_cluster_name"],
            "industry_id": industry_map[row["industry_id"]],
            "customer_id": customer_map.get(row.get("customer_id")) if row.get("customer_id") else None,
        })
        for row in dfs["product_cluster"].to_dict(orient="records")
    ]
    created_product_cluster = ProductCluster.objects.bulk_create(product_cluster)
    product_cluster_map = {uc.product_cluster_name: uc.id for uc in created_product_cluster}

    trademark_group = [
        TrademarkGroup(**{
            "trademark_group_name": row["trademark_group_name"],
            "customer_id": customer_map.get(row.get("customer_id")) if row.get("customer_id") else None,
        })
        for row in dfs["trademark_group"].to_dict(orient="records")
    ]
    created_trademark_group = TrademarkGroup.objects.bulk_create(trademark_group)
    trademark_group_map = {uc.trademark_group_name: uc.id for uc in created_trademark_group}

    productgroup = [
        ProductGroup(**{
            "product_group_name": row["product_group_name"],
            "product_cluster_id": product_cluster_map[row["product_cluster_id"]],
            "customer_id": customer_map.get(row.get("customer_id")) if row.get("customer_id") else None,
        })
        for row in dfs["product_group"].to_dict(orient="records")
    ]
    created_ProductGroup = ProductGroup.objects.bulk_create(productgroup)
    product_group_map = {cat.product_group_name: cat.id for cat in created_ProductGroup}

    product = [
        Product(**{
            "product_name": row["product_name"],
            "product_group_id": product_group_map[row["product_group_id"]],
            "customer_id": customer_map.get(row.get("customer_id")) if row.get("customer_id") else None,
        })
        for row in dfs["product"].to_dict(orient="records")
    ]
    created_Product = Product.objects.bulk_create(product)
    product_map = {cat.product_name: cat.id for cat in created_Product}

    productdescription = [
        ProductDescription(**{
            "product_description_name": row["product_description_name"],
            "product_id": product_map[row["product_id"]],
            "trademark_group_id": trademark_group_map[row["trademark_group_id"]],
            "customer_id": customer_map.get(row.get("customer_id")) if row.get("customer_id") else None,
        })
        for row in dfs["product_description"].to_dict(orient="records")
    ]
    ProductDescription.objects.bulk_create(productdescription)

    buyers = [
        Buyer(
            buyer_name=row["buyer_name"],
            public_own=row.get("public_own"),
            public_holding=row.get("public_holding"),
            holding_name=row.get("holding_name"),
            ticket_own=row.get("ticket_own"),
            ticket_holding=row.get("ticket_holding"),
        )
        for row in dfs["buyer"].to_dict(orient="records")
    ]
    created_buyers = Buyer.objects.bulk_create(buyers)
    buyer_map = {s.buyer_name: s.id for s in created_buyers}

    buyerplants = [
        BuyerPlants(**{
            "buyer_plant_name": row["buyer_plant_name"],
            "buyer_id": buyer_map[row["buyer_id"]],
            "city_id": city_map[row["city_id"]],
            "postalcode": row.get("postalcode"),
            "address": row.get("address"),
        })
        for row in dfs["buyer_plants"].to_dict(orient="records")
    ]
    created_buyerplants = []
    for i in range(0, len(buyerplants), batch_size):
        chunk = buyerplants[i:i + batch_size]
        created_buyerplants.extend(BuyerPlants.objects.bulk_create(chunk, batch_size))

    customerplants = [
        CustomerPlants(**{
            "customer_plant_name": row["customer_plant_name"],
            "customer_id": customer_map[row["customer_id"]],
            "city_id": city_map[row["city_id"]],
            "postalcode": row.get("postalcode"),
            "address": row.get("address"),
        })
        for row in dfs["customer_plants"].to_dict(orient="records")
    ]
    created_customerplants = []
    for i in range(0, len(customerplants), batch_size):
        chunk = customerplants[i:i + batch_size]
        created_customerplants.extend(CustomerPlants.objects.bulk_create(chunk, batch_size))
    customer_plants_map = {cp.customer_plant_name: cp.id for cp in created_customerplants}

    customer_periods = [
        CustomerPeriod(**{
            **row,
            "customer_id": customer_map[row["customer_id"]],
            "year_id": year_map[row["year_id"]],
        })
        for row in dfs["customerperiod"].to_dict(orient="records")
    ]
    CustomerPeriod.objects.bulk_create(customer_periods)


def process_spendcube_sync(df: DataFrame, customer_id: int) -> None:
    print("upload_spendcube started")

    def attach_customerperiod(row, matching: dict[tuple[int, int], int]) -> int:
        return matching[(row["Month"], row["Calendar Year"])]

    with transaction.atomic():
        monthsyears: list[list[int, int]] = df[["Month", "Calendar Year"]].drop_duplicates().values.tolist()
        monthsyears_match: dict[tuple[int, int], int] = {}
        for my in monthsyears:
            obj: QuerySet[CustomerPeriod] = CustomerPeriod.objects.filter(customer_id=customer_id)
            obj = obj.filter(
                Q(begin__year=my[1], begin__month__lte=my[0]) & Q(end__year=my[1], end__month__gte=my[0])
                | Q(begin__year__lt=my[1]) & Q(end__year__gt=my[1])
                | Q(begin__year=my[1], end__year=my[1], begin__month__lte=my[0], end__month__gte=my[0])
            )
            cp: CustomerPeriod = obj[0]
            monthsyears_match[(my[0], my[1])] = cp.id

        df["customerperiod_id"] = df.apply(attach_customerperiod, axis=1, matching=monthsyears_match)
        print("resolving categories started")

        buyer: list[str] = df["Buyer Desc"].unique().tolist()
        buyer_match: dict[str, int] = {}
        num_buyers = len(buyer)
        counter = 0
        for uc in buyer:
            if counter % 25 == 0:
                print("buyer", counter, num_buyers)
            counter += 1
            obj, created = Buyer.objects.get_or_create(buyer_name=uc)
            buyer_match[uc] = obj.id
        df['Buyer Desc'] = df['Buyer Desc'].map(buyer_match).fillna(df['Buyer Desc'])

        granted: list[float] = df["Granted Discount"].tolist()
        for element in granted:
            print(element)

        product_cluster: list[str] = df["Product Cluster"].unique().tolist()
        product_cluster_match: dict[str, int] = {}
        num_product_cluster = len(product_cluster)
        counter = 0
        for uc in product_cluster:
            obj, created = ProductCluster.objects.get_or_create(product_cluster_name=uc)
            product_cluster_match[uc] = obj.id
            if counter % 25 == 0:
                print("product_cluster", counter, num_product_cluster, uc)
            counter += 1
        df['Product Cluster'] = df['Product Cluster'].map(product_cluster_match).fillna(df['Product Cluster'])

        product_group: list[str] = df["Product Group"].unique().tolist()
        product_group_match: dict[str, int] = {}
        num_product_group = len(product_group)
        counter = 0
        for uc in product_group:
            if counter % 25 == 0:
                print("product_group", counter, num_product_group)
            counter += 1
            obj, created = ProductGroup.objects.get_or_create(product_group_name=uc)
            product_group_match[uc] = obj.id
        df['Product Group'] = df['Product Group'].map(product_group_match).fillna(df['Product Group'])

        product: list[str] = df['Product'].unique().tolist()
        product_match: dict[str, int] = {}
        num_product = len(product)
        counter = 0
        for uc in product:
            if counter % 25 == 0:
                print("product", counter, num_product)
            counter += 1
            obj, created = Product.objects.get_or_create(product_name=uc)
            product_match[uc] = obj.id
        df['Product'] = df['Product'].map(product_match).fillna(df['Product'])

        product_description: list[str] = df['Product Desc'].unique().tolist()
        product_desc_match: dict[str, int] = {}
        num_product = len(product_description)
        counter = 0
        for uc in product_description:
            if counter % 25 == 0:
                print("product_description", counter, num_product)
            counter += 1
            obj, created = ProductDescription.objects.get_or_create(product_description_name=uc)
            product_desc_match[uc] = obj.id
        df['Product Desc'] = df['Product Desc'].map(product_desc_match).fillna(df['Product Desc'])

        print("resolving countries started")

        country: list[str] = df['Buyer Demand Country'].unique().tolist()
        country_match: dict[str, int] = {}
        for uc in country:
            obj, created = Country.objects.get_or_create(country_name=uc)
            country_match[uc] = obj.id
        df["Buyer Demand Country"] = df["Buyer Demand Country"].map(country_match).fillna(df["Buyer Demand Country"])

        country: list[str] = df['Seller Offer Country'].unique().tolist()
        country_match: dict[str, int] = {}
        for uc in country:
            obj, created = Country.objects.get_or_create(country_name=uc)
            country_match[uc] = obj.id
        df["Seller Offer Country"] = df["Seller Offer Country"].map(country_match).fillna(df["Seller Offer Country"])

        print("resolving geocoordinates started")
        start_time = time.time()

        spend_cube_cities = set(df["Buyer Demand Location"].unique())
        existing_cities = set(GeoCoordinates.objects.values_list('city', flat=True))
        new_cities = spend_cube_cities - existing_cities
        capitals = GeoCoordinates.objects.filter(capital=True).values('country_id', 'lng', 'lat')
        country_capital_coords = {cap['country_id']: (cap['lng'], cap['lat']) for cap in capitals}

        new_geo_entries = []
        for city in new_cities:
            print(city)
            country_id = df.loc[df["Buyer Demand Location"] == city, "Buyer Demand Country"].iloc[0]
            if country_id in country_capital_coords:
                lng, lat = country_capital_coords[country_id]
                new_geo_entries.append(GeoCoordinates(country_id=country_id, city=city, lng=lng, lat=lat, capital=False))
                coordinates = {"longitude": lng, "latitude": lat}
                country_name = Country.objects.get(id=country_id).country_name
                log_default_value_to_excel(
                    'GeoCoordinates',
                    default_values=str(coordinates),
                    country_name=country_name,
                    city_name=city,
                )

        buyer_demand_location: list[str] = df["Buyer Demand Location"].unique().tolist()
        buyer_demand_location_match: dict[str, int] = {}
        num_buyer_demand_location = len(buyer_demand_location)
        counter = 0
        start_time = time.time()
        for uc in buyer_demand_location:
            obj, created = GeoCoordinates.objects.get_or_create(city=uc)
            buyer_demand_location_match[uc] = obj.id
            if counter % 25 == 0:
                print("city", counter, num_buyer_demand_location, uc)
            counter += 1
        df['Buyer Demand Location'] = df['Buyer Demand Location'].map(buyer_demand_location_match).fillna(df['Buyer Demand Location'])

        buyer_plant_match: dict[str, int] = {}
        num_buyers_plants = len(df["Buyer Plant"].unique())
        counter = 0
        for _, row in df[["Buyer Plant", "Buyer Desc", "Buyer Demand Location"]].drop_duplicates().iterrows():
            plant_name = row["Buyer Plant"]
            if plant_name in buyer_plant_match:
                continue
            if counter % 25 == 0:
                print("buyer_plant", counter, num_buyers_plants)
            counter += 1
            obj, created = BuyerPlants.objects.get_or_create(
                buyer_plant_name=plant_name,
                defaults={
                    "buyer_id": row["Buyer Desc"],
                    "city_id": row["Buyer Demand Location"],
                },
            )
            buyer_plant_match[plant_name] = obj.id
        df['Buyer Plant'] = df['Buyer Plant'].map(buyer_plant_match).fillna(df['Buyer Plant'])

        seller_offer_location: list[str] = df["Seller Offer Location"].unique().tolist()
        seller_offer_location_match: dict[str, int] = {}
        num_seller_offer_location = len(seller_offer_location)
        counter = 0
        start_time = time.time()
        for uc in seller_offer_location:
            obj, created = GeoCoordinates.objects.get_or_create(city=uc)
            seller_offer_location_match[uc] = obj.id
            if counter % 25 == 0:
                print("city", counter, num_seller_offer_location, uc)
            counter += 1
        df['Seller Offer Location'] = df['Seller Offer Location'].map(seller_offer_location_match).fillna(df['Seller Offer Location'])

        if new_geo_entries:
            GeoCoordinates.objects.bulk_create(new_geo_entries)

        end_time = time.time()
        print("resolving geocoordinates ended", end_time - start_time)

        df.drop(["Month", "Currency Local", "Calendar Year"], axis=1, inplace=True)

        df.rename({
            "New Spend": "spend",
            "PPM": "fault_ppm",
            "Buyer Demand Location": "address_buyer_id",
            "Seller Offer Location": "address_customer_id",
            "Buyer Demand Country": "country_buyer_id",
            "Seller Offer Country": "country_customer_id",
            "Product Cluster": "product_cluster_id",
            "Product Group": "product_group_id",
            "Product": "product_id",
            "Product Desc": "product_description_id",
            "Buyer Desc": "buyer_id",
            "Buyer Plant": "buyer_plant_id",
            "Granted Discount": "granted_discount",
            "Quantity": "quantity",
        }, axis=1, inplace=True)

        df["name"] = ""

    print("engine started")
    start_time = time.time()

    db_user = os.environ.get("DJANGO_DB_USER", "")
    password = os.environ.get("DJANGO_DB_PASSWORD", "")
    host = os.environ.get("DJANGO_DB_HOST", "")
    port = os.environ.get("DJANGO_DB_PORT", "5432")
    dbname = os.environ.get("DJANGO_DB_NAME", "")

    conn = psycopg2.connect(
        dbname=dbname, user=db_user, password=password, host=host, port=port
    )
    cur = conn.cursor()

    table_name = 'siapp_itemstocustomerperiods'

    target_columns = [
        'name', 'product_cluster_id', 'product_group_id', 'product_id',
        'product_description_id', 'buyer_id', 'buyer_plant_id',
        'customerperiod_id', 'spend', 'quantity', 'fault_ppm',
        'address_buyer_id', 'country_buyer_id', 'address_customer_id',
        'country_customer_id', 'granted_discount',
    ]
    df = df[target_columns]

    def insert_in_batches(df, batch_size=50000):
        for start in range(0, len(df), batch_size):
            end = min(start + batch_size, len(df))
            batch = df.iloc[start:end]
            buffer = StringIO()
            batch.to_csv(buffer, index=False, header=False, na_rep='', float_format='%.4f')
            buffer.seek(0)
            try:
                cur.copy_from(buffer, table_name, sep=',', null='', columns=target_columns)
                conn.commit()
                print(f"{start} von {len(df)} Datensätzen erfolgreich eingefügt.")
            except Exception as e:
                conn.rollback()
                print(f"Fehler beim Einfügen von Batch {start}-{end}: {e}")

    insert_in_batches(df, batch_size=50000)

    cur.close()
    conn.close()

    end_time = time.time()
    print("engine ended", end_time - start_time)


def upload_db(file: UploadedFile, bcc_cem_csv: UploadedFile = None) -> JsonResponse:
    print("start read")
    filename_extension = os.path.splitext(str(file))[1]
    start_time = time.time()

    if filename_extension not in ('.xlsx', '.xlsb', '.xls', '.xlsm'):
        return JsonResponse({"error": "File type not supported."}, status=400)

    dfs = pd.read_excel(file, engine="calamine", sheet_name=None)

    if bcc_cem_csv is not None:
        bcc_cem_csv.seek(0)
        csv_text = bcc_cem_csv.read().decode("utf-8")
        dfs["bcc_cem"] = pd.read_csv(
            StringIO(csv_text),
            sep=";",
            decimal=",",
            engine="python",
            on_bad_lines="warn",
        )

    try:
        end_time = time.time()
        print("read time", end_time - start_time)
        redis_cache.empty_cache()
        process_db_sync(dfs)
    except ValidationError as e:
        return JsonResponse({"error": str(e.messages[0])}, status=400)

    return JsonResponse({"success": "File uploaded successfully. You now need to reimport the spend cube."}, status=200)


def upload_spendcube(file: UploadedFile, customer_id: int) -> JsonResponse:
    df: DataFrame

    filename_extension = os.path.splitext(str(file))[1]

    if filename_extension == ".xlsx":
        if file.content_type == "application/vnd.ms-excel.sheet.binary.macroenabled.12":
            df = pd.read_excel(file, engine="calamine", sheet_name="Raw Data")
        else:
            df = pd.read_excel(file, engine="openpyxl", sheet_name="Raw Data")
    elif filename_extension == ".csv":
        df = pd.read_csv(file, encoding='utf-8')
    else:
        return JsonResponse({"error": "File type not supported."}, status=400)

    mandatory_columns: list[str] = [
        "Product Cluster", "Product Group", "Product", "Product Desc",
        "New Spend", "Buyer Demand Location", "Buyer Demand Country",
        "Seller Offer Location", "Buyer Desc", "PPM", "Month",
        "Calendar Year", "Granted Discount", "Seller Offer Country",
        "Buyer Plant", "Quantity",
    ]
    for col in mandatory_columns:
        if col not in df.columns:
            return JsonResponse({"error": f"Column '{col}' missing"}, status=400)

    try:
        process_spendcube_sync(df, customer_id)
    except ValidationError as e:
        return JsonResponse({"error": str(e.messages[0])}, status=400)

    return JsonResponse({"success": "File uploaded successfully"}, status=200)


@router_upload.post("/uploadspendcube/", auth=JWTAuth())
def upload_spendcube_view(request: HttpRequest, file: UploadedFile = File(...)):
    if not is_manager_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    user = request.user
    if not hasattr(user, 'customer') or user.customer is None:
        return JsonResponse({"error": "User does not have a customer."}, status=400)

    return upload_spendcube(file, user.customer.id)


@router_upload.post("/uploaddb/", auth=JWTAuth())
def upload_db_view(request: HttpRequest, file: UploadedFile = File(...)):
    if not is_manager_or_above(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    return upload_db(file)
