# Canteen Pre-Order System — Backend

CS612 Group 4 — SOA backend built with **FastAPI + PostgreSQL + SQLAlchemy + JWT**.

Demo 1 scope: authentication with role-based access, profile, menu, inventory, cart,
placing a pre-order (with an order ID) and an incoming-orders list for staff.

## Project structure

```
app/
  main.py            FastAPI app, registers every service router
  config.py          Settings loaded from .env
  database/          Engine/session (database.py) + SQLAlchemy models (models.py)
  auth/              Register, login, JWT, password hashing, role checks
  users/             Profile
  menu/              Menu, categories, search/filter
  inventory/         Stock & availability rules
  cart/              Cart and cart items
  orders/            Place an order, order history, order details
  staff/             Staff-only incoming orders
seed.py              Seeds roles, staff account, menu
```

## Run locally

Prerequisites: Python 3.9+ and PostgreSQL.

```bash
# 1. Create the database
createdb canteen            # or: psql -U postgres -c "CREATE DATABASE canteen;"

# 2. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env        # then set DATABASE_URL and JWT_SECRET

# 4. Create tables + seed data (safe to re-run)
python seed.py

# 5. Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs (Swagger): http://localhost:8000/docs

> `localhost`, `10.0.2.2` and LAN IPs only work for devices on **your** machine or Wi-Fi.
> A frontend developer working elsewhere needs a public URL; see below.

## Sharing the backend with a remote frontend developer

The Android developer needs a public **HTTPS** base URL. Choose one option:

### Option A: Permanent free hosting (Render + Neon + UptimeRobot)

Gives one fixed HTTPS URL that works 24/7 from anywhere. Your laptop can be off. Everything
uses free plans only.

| Part | Service (free plan) | Purpose |
|---|---|---|
| API | [Render](https://render.com) web service | Runs FastAPI at `https://<name>.onrender.com` |
| Database | [Neon](https://neon.tech) PostgreSQL | Cloud database (no expiry). It can be opened in pgAdmin. |
| Keep-awake | [UptimeRobot](https://uptimerobot.com) | Pings `/` every 5 min so the free Render service doesn't sleep |

1. **Neon:** sign up → create a project (region: Asia Pacific / Singapore) → copy the
   connection string (`postgresql://...neon.tech/neondb?sslmode=require...`).
2. **Render:** sign in with GitHub → **New → Blueprint** → select this repo. `render.yaml`
   asks for:
   - `DATABASE_URL`: paste the Neon connection string
   - `SEED_STAFF_PASSWORD`: e.g. `Staff@123`

   On every start, the service creates the tables and seeds the menu and staff account.
3. **UptimeRobot:** add an **HTTP(s)** monitor for `https://<name>.onrender.com/` with a
   5-minute interval.
4. Share with the team:
   - Base URL: `https://<name>.onrender.com`
   - API docs: `https://<name>.onrender.com/docs`
   - OpenAPI (Postman → Import → Link): `https://<name>.onrender.com/openapi.json`

Pushing to the `main` branch redeploys automatically; the URL never changes.

**pgAdmin → Neon:** Register → Server. Use the host, database, user and password from the
Neon connection string, port `5432`, and on the **Parameters** tab set *SSL mode* = `require`.

### Option B: Tunnel from your laptop (local PostgreSQL + pgAdmin)

One command starts PostgreSQL (if it's stopped), the API and a public HTTPS tunnel:

```bash
./start.sh            # prints PUBLIC API URL: https://xxxx.trycloudflare.com
./start.sh --local    # API only, http://localhost:8000
```

Manual equivalent:

Start the server and expose it publicly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# in another terminal (brew install cloudflared):
cloudflared tunnel --url http://localhost:8000
# or: ngrok http 8000
```

Share the printed `https://....trycloudflare.com` URL. Your laptop must stay on with
the server running, and the URL changes every time the tunnel restarts.

### Android integration notes

- Use the **HTTPS** URL. Android blocks plain `http://` by default.
- Add `<uses-permission android:name="android.permission.INTERNET"/>` to the manifest.
- Send JSON bodies with `Content-Type: application/json`.
- Save `access_token` after login (e.g. DataStore) and send
  `Authorization: Bearer <token>` on protected calls. Tokens last 24 h by default.
- Route the user to the student or staff screens based on the `role` returned at login.
- On a 401 response, send the user back to the login screen.
- Show the `detail` field of error responses to the user.

### Run with Docker (API and PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
```

## Seed data

| What | Value |
|---|---|
| Roles | STUDENT, FACULTY, CANTEEN_STAFF, ADMIN |
| Staff account | Institute ID `STAFF001` / `Staff@123` (no self-registration for staff) |
| Menu | Veg Biryani ₹80 (25), Masala Dosa ₹50 (30), Chicken Roll ₹70 (20), Samosa ₹20 (50), Tea ₹15 (100), Coffee ₹25 (50) |

Anyone can register with a new Institute ID; the account is created with the STUDENT role.
To make someone FACULTY / CANTEEN_STAFF / ADMIN, change their `role_id` in the `users` table
(1 STUDENT, 2 FACULTY, 3 CANTEEN_STAFF, 4 ADMIN).

## Authentication

1. `POST /auth/login` (Institute ID + password) returns `access_token`.
2. Send the token on every protected request:
   `Authorization: Bearer <access_token>`
3. Logout happens on the client: delete the stored token.

In Swagger, click **Authorize** and paste the token.

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | – | Create an account: Institute ID, Username, Password, Confirm Password |
| POST | `/auth/login` | – | Login with Institute ID + password; returns JWT and role |
| GET | `/auth/me` | User | Current user |
| POST | `/auth/logout` | User | Client-side logout acknowledgement |
| GET | `/users` | CANTEEN_STAFF / ADMIN | List all registered users |
| GET | `/users/me` | User | Profile |
| GET | `/menu` | – | Menu; query params: `search`, `category_id`, `available_only` |
| GET | `/menu/categories` | – | Categories |
| GET | `/menu/{food_id}` | – | One food item |
| GET | `/inventory/{food_id}` | – | Stock + availability |
| GET | `/cart` | User | Cart with subtotal/total |
| POST | `/cart/items` | User | Add item `{food_id, quantity}` |
| PUT | `/cart/items/{item_id}` | User | Change quantity `{quantity}` |
| DELETE | `/cart/items/{item_id}` | User | Remove item |
| DELETE | `/cart` | User | Clear cart |
| POST | `/orders` | User | Place an order from the cart |
| GET | `/orders` | User | My order history |
| GET | `/orders/{order_id}` | User | Order details (e.g. `ORD-20261010-0001`) |
| GET | `/staff/orders` | CANTEEN_STAFF / ADMIN | Incoming orders (`?status=PLACED`) |

### Example requests

```jsonc
// POST /auth/register
{ "institute_id": "2621532", "username": "umar", "password": "Umar@123", "confirm_password": "Umar@123" }

// POST /auth/login
{ "institute_id": "2621532", "password": "Umar@123" }
// -> { "access_token": "...", "token_type": "bearer", "role": "STUDENT", "user_id": 2, "institute_id": "2621532", "username": "umar" }

// POST /cart/items
{ "food_id": 1, "quantity": 2 }

// POST /orders   (no body)
// -> { "order_id": "ORD-20261010-0001", "status": "PLACED", "total_amount": 160.0, "items": [...], "message": "Order placed successfully" }
```

Errors always look like `{ "detail": "..." }`, using these status codes:
400 (empty cart), 401 (not logged in / bad credentials), 403 (wrong role),
404 (not found), 409 (duplicate / out of stock), 422 (invalid input).

## Business rules implemented

- Passwords are hashed with Argon2; plaintext passwords are never stored.
- Self-registration creates STUDENT accounts; Institute ID and username must be unique, and Password must equal Confirm Password. Staff accounts are seeded or created by an admin.
- Role-based access: a student token on `/staff/orders` returns **403 Forbidden**.
- An item becomes unavailable automatically when its quantity reaches 0.
- The cart and orders cannot exceed the available stock.
- Placing an order runs as one transaction: lock the cart, lock the inventory rows
  (`SELECT … FOR UPDATE`), check stock, create the order and its items, reduce
  inventory, then clear the cart.
- Repeated "place order" taps cannot create duplicate orders, because the cart is locked and then cleared.
- Order items store the price at the time of the order.
- Customers can only see their own orders.

## Not in Demo 1 (planned)

Payment, pickup slots, the full order status flow (ACCEPTED → PREPARING → READY → COLLECTED),
pickup verification, cancellation, notifications, feedback, reports, admin management.
