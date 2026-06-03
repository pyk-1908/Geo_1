# Demo data, database schema & Salesforce schema

Reference for the Salesforce-notes-on-map demo. The local data + users are created by
`python manage.py seed_demo` (see [SETUP.md](SETUP.md)); the Salesforce notes live in the
shared cloud org.

---

## 1. Login users (created by `seed_demo`)

| User | Password | Purpose |
|---|---|---|
| `mapuser` | `MapTest1234!` | App login — Managers group + customer, can load the map |
| `admin` | `Admin@12345` | Django admin (`/admin/`) — superuser |

> Local **demo** credentials only — not real secrets.

---

## 2. Demo buyers (local DB) and their Salesforce link

All buyers belong to customer **Demo Customer**, period **2025**, product chain
**Electronics → Sensors → Pressure Sensor**. On the map, pick that chain, then switch
**country** between Germany and United States.

| Buyer | `salesforce_account_id` | Country | City (lat, lng) | Notes shown on click |
|---|---|---|---|---|
| Edge Communications | `001g500000NHU7mAAH` | Germany | Berlin (52.52, 13.40) | **5** |
| Burlington Textiles Corp | `001g500000NHU7nAAH` | Germany | Munich (48.137, 11.575) | **3** |
| Pyramid Construction | `001g500000NHU7oAAH` | Germany | Frankfurt (50.11, 8.68) | **2** |
| Mueller Logistik GmbH | _(none)_ | Germany | Hamburg (53.55, 9.99) | no notes section (unlinked) |
| Grand Hotels & Resorts | `001g500000NHU7qAAH` | United States | New York (40.71, -74.01) | **2** |
| Dickenson plc | `001g500000NHU7pAAH` | United States | Los Angeles (34.05, -118.24) | **2** |

> The **Growth** column on the map is `growth_score`, generated randomly per request
> (`random.randint(0, 100)`) — it's a placeholder, so it changes on each load. **# of Plants**
> is the buyer's distinct plant locations (1 each here).

---

## 3. Salesforce notes per account (in the shared org)

These are `Note` records (legacy), linked to each Account by `ParentId`. Created via the
`sf` CLI for the demo.

| Account (Id) | Notes |
|---|---|
| Edge Communications (`001g500000NHU7mAAH`) | Quarterly review · Contract signed · Berlin Site Visit · Q2 Renewal Discussion · Backend Integration Test |
| Burlington Textiles Corp (`001g500000NHU7nAAH`) | Quality audit passed · Payment terms · New RFQ received |
| Pyramid Construction (`001g500000NHU7oAAH`) | Logistics note · Discovery call |
| Dickenson plc (`001g500000NHU7pAAH`) | Reference call · Trade show lead |
| Grand Hotels & Resorts (`001g500000NHU7qAAH`) | Volume forecast · Onboarding kickoff |

---

## 4. How a map buyer connects to its Salesforce notes

```
Buyer.salesforce_account_id  ──►  Salesforce Account.Id  ──►  Account's Notes
        (local DB)                    (cloud org)              (Note + ContentVersion)
```

Flow: the buyer-map API returns each buyer's `salesforce_account_id` → the marker carries it
→ on popup open the frontend calls `GET /api/salesforce/notes/?account_id=<id>` →
`get_notes_for_account()` queries Salesforce and returns `[{title, body, created_date}]`.

---

## 5. Database schema (relevant models)

App models live in `backend/siapp/models.py`. The models that drive the map + notes link:

**`Buyer`** — a company that buys.
- `buyer_name` (unique), `public_own`, `public_holding`, `holding_name`, `ticket_own`, `ticket_holding`
- `salesforce_account_id` (CharField 18, nullable, indexed) ← **added for this feature**

**`ItemsToCustomerPeriods`** — the fact table the map reads (one row per buyer/product/period/location).
- FKs: `buyer`, `buyer_plant`, `customerperiod`, `product`, `product_group`, `product_cluster`,
  `product_description`, `address_buyer`→`GeoCoordinates`, `country_buyer`→`Country`,
  `address_customer`→`GeoCoordinates`, `country_customer`→`Country`
- `spend` (BigInt), `quantity` (Float), `fault_ppm`, `granted_discount`

**`GeoCoordinates`** — a city location. `country`→`Country`, `city`, `lat`, `lng`, `capital`, `state`.

**`BuyerPlants`** — a buyer's plant. `buyer_plant_name`, `buyer`→`Buyer`, `city`→`GeoCoordinates`.

**`Customer`** — the logged-in user's company. `customer_name`. `User.customer`→`Customer`.

**`CustomerPeriod`** — a date range. `customer`, `begin`, `end`, `name`, `year`→`Year`.

**Product hierarchy:** `Industry` → `ProductCluster` → `ProductGroup` → `Product` (→ `ProductDescription`, `TrademarkGroup`).

**Geography:** `Continent` → `Region` → `Country` (`country_name`, `country_code`).

**`User`** (extends `AbstractUser`): `customer`→`Customer`, `email`. "Employees"/"Managers" groups gate access.

### Buyer-map API response shape (`GET /api/buyer/buyer_map/`)
```json
{
  "country": [{
    "country_name": "Germany", "country_id": 1, "country_code": "de",
    "buyers": [{
      "buyer_name": "Edge Communications", "buyer_id": 1,
      "salesforce_account_id": "001g500000NHU7mAAH",
      "growth_score": 78, "num_plants_abs": 1,
      "locations": [{ "city_name": "Berlin", "city_id": 1, "lat": 52.52, "lng": 13.40, "state_name": "Berlin" }]
    }],
    "seller": { "seller_name": "Demo Customer", "seller_id": 1, "locations": [] }
  }]
}
```

---

## 6. Salesforce schema (objects used for notes)

`get_notes_for_account(account_id)` reads two note types and merges them, newest first:

**`Account`** — `Id` (15/18-char), `Name`. A `Buyer.salesforce_account_id` points here.

**`Note`** (legacy / "Notes & Attachments") — used for the demo notes.
- `Title`, `Body`, `CreatedDate`, `ParentId` (→ Account)
- Query: `SELECT Title, Body, CreatedDate FROM Note WHERE ParentId = :account_id`

**`ContentVersion`** (modern "Enhanced Notes" are stored here as `FileType = 'SNOTE'`).
- `Title`, `TextPreview`, `CreatedDate`, `FileType`, `IsLatest`, `ContentDocumentId`
- Linked to an account via **`ContentDocumentLink`** (`LinkedEntityId` → Account, `ContentDocumentId`).
- Two-step query: find the account's `ContentDocumentId`s via `ContentDocumentLink`, then fetch the
  SNOTE `ContentVersion`s. (We use `ContentVersion`, not `ContentNote`, because `ContentNote` is not
  available in this trial org.)

**Auth:** the backend connects with OAuth Client Credentials via an **External Client App**
(`SF_AUTH_METHOD=client_credentials`, `SF_CONSUMER_KEY`/`SF_CONSUMER_SECRET`, `SF_DOMAIN` = My Domain
host without `.salesforce.com`).
