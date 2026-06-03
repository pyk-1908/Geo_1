# Local setup — running GeoProject (with the Salesforce notes map) on a fresh machine

What lives where:
- **Salesforce notes** → in the shared cloud org. Already there, nothing to re-add.
- **Local app data** (buyers, `salesforce_account_id` links, login users) → in `backend/db.sqlite3`,
  which is **gitignored**. A fresh clone starts empty, so you re-seed it (step 4).

## Prerequisites
- Python 3.12, Node.js + npm, Git.

## 1. Clone
```bash
git clone <repo-url>
cd geo
git checkout salesforce-notes-on-map   # until merged to master
```

## 2. Backend dependencies
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## 3. Backend config — `backend/.env`
Copy `backend/.env.example` to `backend/.env` and set at least:
```ini
ENV=DEV_LOCAL
SECRET_KEY=any-non-empty-value
# Salesforce (Client Credentials via the External Client App):
SF_AUTH_METHOD=client_credentials
SF_DOMAIN=orgfarm-6c831b9622-dev-ed.develop.my   # My Domain WITHOUT ".salesforce.com"
SF_CONSUMER_KEY=<copy from a teammate, securely>
SF_CONSUMER_SECRET=<copy from a teammate, securely>
```
> `.env` is gitignored — get `SF_CONSUMER_KEY` / `SF_CONSUMER_SECRET` from someone who has them
> (password manager / secure channel), never via git or chat. `ENV=DEV_LOCAL` uses SQLite, so no
> Postgres/Redis needed.

## 4. Create DB + seed demo data and users
```bash
python manage.py migrate
python manage.py seed_demo
```
`seed_demo` creates the buyers (Germany + USA) with their Salesforce links, plus the logins:
- **app:** `mapuser` / `MapTest1234!` (can load the map)
- **admin:** `admin` / `Admin@12345` (`/admin/`)

## 5. Frontend
```bash
cd ../frontend
npm install
```

## 6. Run
```bash
# backend (from backend/, venv active)
python manage.py runserver            # http://localhost:8000

# frontend (from frontend/)
npm run dev                           # http://localhost:5173
```
If those ports are taken, use alternates and point the frontend at the backend:
```bash
python manage.py runserver 8010
VITE_PORT=5180 VITE_API_TARGET=http://localhost:8010 npm run dev
```

## 7. Try it
Open the frontend URL, log in as `mapuser` / `MapTest1234!`, on the map pick
**Electronics → Sensors → Pressure Sensor**, switch country between **Germany** and **United States**,
and click a buyer marker — its popup shows that buyer's Salesforce notes.

## Not required
- The `sf` Salesforce CLI — optional, only to add/inspect notes. The app reaches Salesforce via the
  Consumer Key/Secret in `.env`.
- Postgres / Redis — only used when `ENV` is not `DEV_LOCAL`.
