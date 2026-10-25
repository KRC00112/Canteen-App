# Canteen Pre-Order System — Backend

CS612 Group 4 — SOA backend built with **FastAPI + PostgreSQL + SQLAlchemy + JWT**.

Demo 1 scope: authentication with role-based access, profile, food items, inventory, cart,
placing a pre-order (with an order ID) and an incoming-orders list for staff.

## Project structure

```
app/
  main.py            FastAPI app, registers every service router
  config.py          Settings loaded from .env
  database/          Engine/session, models, add-column migrations, DB views
  auth/              Register, login, JWT, password hashing, role checks
  users/             Profile
  items/             Food items, categories, search/filter (Veg/Non-Veg, price)
  inventory/         Stock rules: cart holds, low-stock limits, stock status
  cart/              Cart and cart items
  orders/            Place an order, order history, order details
  staff/             Staff-only incoming orders, inventory and food item editing
  notifications/     In-app notifications and "Notify me" stock alerts
seed.py              Seeds roles, staff and admin accounts, food items
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

   On every start, the service creates the tables and seeds the food items, staff and admin accounts.
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
- Use the student or faculty register/login endpoint for the screen the user picked
  (e.g. a "Student / Faculty" toggle), and route by the `role` returned at login.
- On a 401 response, send the user back to the login screen.
- Show the `detail` field of error responses to the user.

### Run with Docker (API and PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
```

## Who manages what

| | Admin | Canteen staff |
|---|---|---|
| Food items: create, edit, price, remove (`/admin/items`) | ✅ | – |
| Stock / restock (`PUT /staff/inventory`) | – | ✅ |
| Customers' carts (`GET /staff/carts`) | – | ✅ |
| Incoming orders (`GET /staff/orders`) | ✅ | ✅ |
| Approve / deactivate staff (`/admin/staff`) | ✅ | – |
| All users, customer details, orders, logins (`/admin/*`) | ✅ | – |

## Seed data

| What | Value |
|---|---|
| Roles | STUDENT, FACULTY, CANTEEN_STAFF, ADMIN |
| Staff account | Institute ID `STAFF001` / `Staff@123` (more staff register at `/auth/staff/register` and need admin approval) |
| Admin account | Institute ID `ADMIN001` / `Admin@123`: the one permanent main canteen admin (set `SEED_ADMIN_PASSWORD` to change). No registration; a unique index (`uq_users_single_admin`) stops the database from ever holding a second ADMIN |
| Food items | Veg Biryani ₹80 (25), Masala Dosa ₹50 (30), Chicken Roll ₹70 (20, **Non-Veg**), Samosa ₹20 (50), Tea ₹15 (100), Coffee ₹25 (50). All others are Veg; each has ingredients and an average cooking time |

Students register via `/auth/student/register` (STUDENT role) and faculty via
`/auth/faculty/register` (FACULTY role) and staff via `/auth/staff/register` (CANTEEN_STAFF role,
**PENDING** until the admin approves it at `POST /admin/staff/{user_id}/approve`). The one admin can't register; it is seeded.
To change someone's role, update their `role_id` in the `users` table
(1 STUDENT, 2 FACULTY, 3 CANTEEN_STAFF, 4 ADMIN).

## Authentication

1. Log in with Institute ID + password at the endpoint for the account type. It returns `access_token`:

   | Who | Register | Login |
   |---|---|---|
   | Student | `POST /auth/student/register` | `POST /auth/student/login` |
   | Faculty | `POST /auth/faculty/register` | `POST /auth/faculty/login` |
   | Canteen staff | `POST /auth/staff/register` (then admin approval) | `POST /auth/staff/login` |
   | Main canteen admin | – (seeded) | `POST /auth/admin/login` |

   Using the wrong login (e.g. a faculty account on the student login) returns **403**
   "This is a Faculty account, not a Student account. Please use the Faculty login".
   The old `POST /auth/register` (creates a student) and `POST /auth/login` (any account) still work.
2. Send the token on every protected request:
   `Authorization: Bearer <access_token>`
3. `POST /auth/logout` ends the session on the server; the app should also delete the stored token.

In Swagger, click **Authorize** and paste the token.

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/student/register` | – | Create a STUDENT account: Institute ID, Username, Password, Confirm Password |
| POST | `/auth/faculty/register` | – | Create a FACULTY account (same fields) |
| POST | `/auth/student/login` | – | Student login (Institute ID + password); returns JWT and role. Other account types get 403 |
| POST | `/auth/faculty/login` | – | Faculty login; other account types get 403 |
| POST | `/auth/staff/register` | – | Create a CANTEEN_STAFF account (same fields). It is PENDING, and login returns 403 "waiting for admin approval" until the admin approves it |
| POST | `/auth/staff/login` | – | Canteen staff login; other account types get 403 |
| POST | `/auth/admin/login` | – | Main canteen admin login; other account types get 403 |
| POST | `/auth/login` | – | Login for any account type (staff/admin use this) |
| POST | `/auth/register` | – | *Deprecated*: same as `/auth/student/register` |
| GET | `/auth/me` | User | Current user |
| POST | `/auth/logout` | User | End the current session (token stops working) |
| GET | `/users` | CANTEEN_STAFF / ADMIN | All registered users with login status (`is_logged_in`, `active_sessions`, `last_login_at`, ...); filter with `?role=STUDENT` / `FACULTY` / ... |
| GET | `/users/logged-in` | CANTEEN_STAFF / ADMIN | All currently logged-in users and their sessions |
| GET | `/users/me` | User | Profile |
| GET | `/items` | – (token optional) | Food items; query params: `search`, `category_id`, `food_type` (`VEG` / `NON_VEG`), `min_price`, `max_price`, `available_only` |
| GET | `/items/categories` | – | Categories, each with the food types it contains |
| GET | `/items/{food_id}` | – (token optional) | One food item. (`/menu`, `/menu/categories` and `/menu/{food_id}` still work for older app builds, but are hidden from the docs) |
| GET | `/inventory/{food_id}` | – (token optional) | Availability + stock status (no exact count) |
| GET | `/cart` | User | Cart with subtotal/total |
| POST | `/cart/items` | User | Add item `{food_id, quantity}` |
| PUT | `/cart/items/{item_id}` | User | Change quantity `{quantity}` |
| DELETE | `/cart/items/{item_id}` | User | Remove item |
| DELETE | `/cart` | User | Clear cart |
| POST | `/orders` | User | Place an order from the cart |
| GET | `/orders` | User | My order history |
| GET | `/orders/{order_id}` | User | Order details (e.g. `ORD-20261010-0001`) |
| GET | `/staff/orders` | CANTEEN_STAFF / ADMIN | Incoming orders (`?status=PLACED`) |
| GET | `/staff/inventory` | CANTEEN_STAFF / ADMIN | Exact stock, units held in carts, units ordered in the last 24 h |
| PUT | `/staff/inventory/{food_id}` | CANTEEN_STAFF | Set stock `{quantity, available?}` (restock). Staff only |
| GET | `/staff/carts` | CANTEEN_STAFF | Every customer's current cart, with stock holds. Staff only |
| GET | `/admin/users` | ADMIN | Every account with login status (`?role=STUDENT` / ...) |
| GET | `/admin/users/{user_id}` | ADMIN | Full customer details: profile, login history, orders, total spent, notifications, stock alerts |
| GET | `/admin/orders` | ADMIN | Every order (`?status=PLACED`, `?user_id=3`) |
| GET | `/admin/orders/{order_id}` | ADMIN | Any order with the customer who placed it |
| GET | `/admin/sessions` | ADMIN | Login history of every account: device, IP, login/logout times (`?active_only=true`) |
| GET | `/admin/notifications` | ADMIN | Notifications sent to every user (`?user_id=3`) |
| GET | `/admin/stock-alerts` | ADMIN | Every customer's "Notify me" request |
| GET | `/admin/staff` | ADMIN | Staff accounts (`?status=PENDING` = waiting for approval) |
| POST | `/admin/staff/{user_id}/approve` | ADMIN | Approve a pending staff account (or re-activate one) |
| POST | `/admin/staff/{user_id}/deactivate` | ADMIN | Reject / block a staff account; their logins end immediately |
| POST | `/admin/items` | ADMIN | Add a food item: `name`, `price`, `category` (new categories are created), optional `description`, `food_type`, `ingredients`, `avg_cooking_time_minutes`. It starts with 0 stock until staff restock it |
| PATCH | `/admin/items/{food_id}` | ADMIN | Edit `name`, `price`, `description`, `category`, `food_type`, `ingredients`, `avg_cooking_time_minutes` (only the fields sent). Past orders keep their price |
| DELETE | `/admin/items/{food_id}` | ADMIN | Remove an item. Past orders still show it; it is taken out of carts (customers get an `ITEM_REMOVED` notification) |
| GET | `/notifications` | User | My notifications + `unread_count` (`?unread_only=true`) |
| POST | `/notifications/{id}/read` | User | Mark one as read |
| POST | `/notifications/read-all` | User | Mark all as read |
| GET | `/notifications/stock-alerts` | User | Items I asked to be notified about |
| POST | `/notifications/stock-alerts` | User | "Notify me" `{food_id}` for a sold-out / fully reserved item |
| DELETE | `/notifications/stock-alerts/{food_id}` | User | Cancel "Notify me" |

### Example requests

```jsonc
// POST /auth/student/register   (faculty: POST /auth/faculty/register, same body)
{ "institute_id": "2621532", "username": "umar", "password": "Umar@123", "confirm_password": "Umar@123" }
// -> { "message": "Student account created successfully", "user_id": 2, "institute_id": "2621532", "username": "umar", "role": "STUDENT" }

// POST /auth/student/login   (faculty: POST /auth/faculty/login)
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

## Live activity (demo / debugging)

Every API call is logged as one readable line: time (IST), method, path, status, duration,
who called it, and what happened. Passwords, tokens and request bodies are never logged.

```
12:07:53  POST   /orders                            201    15ms  umar (STUDENT)  Order ORD-20261024-0001 placed: Rs 210.00, ready in ~20 min; Veg Biryani x2 (stock 25->23), Masala Dosa x1 (stock 30->29)
12:07:53  POST   /auth/staff/login                  403    24ms  cook1 (CANTEEN_STAFF)  Your staff account is waiting for admin approval
```

Three ways to watch it while the app is used:

| Where | How |
|---|---|
| Terminal (VS Code) | `brew install render && render login` once, then `./live-logs.sh srv-xxxxxxxx` (service ID from the Render dashboard URL); later just `./live-logs.sh` |
| Browser | `https://canteen-backend-xzko.onrender.com/admin/live`, log in with the admin account. Live table plus counters (logged in, users, orders today, pending staff) |
| Render dashboard | Service → **Logs** |

`GET /admin/live/feed?after=<id>` (ADMIN) returns the same entries as JSON. The live page keeps
the last 500 calls in memory, so it starts empty after a restart or deploy.
Health checks (`/`) and the live page's own polling are not logged.

## Browsing users in the database

Read-only views are created automatically (PostgreSQL). In pgAdmin they're under
**Schemas → public → Views**; in the Neon console, query them in the **SQL Editor**:

| View | Shows |
|---|---|
| `users_overview` | Every registered user and their login status: `is_logged_in`, `active_sessions`, `total_logins`, `last_login_at`, `last_seen_at` |
| `logged_in_users` | Only the users logged in right now, one row per active login (device, IP, login time) |
| `orders_overview` | Every order, newest first: customer, total, items (`Veg Biryani x2, ...`), placed / ready times |
| `admin_account` | The one permanent main canteen admin account and its login status |
| `items_overview` | Every food item with category, `food_type` (VEG / NON_VEG), price, cooking time, ingredients and stock |

```sql
SELECT * FROM users_overview;
SELECT * FROM logged_in_users;
SELECT * FROM admin_account;
SELECT * FROM orders_overview;
SELECT * FROM items_overview;
```

New columns on existing tables are added automatically on start (`app/database/migrations.py`),
so the Neon database upgrades itself on the next deploy.

## Food items: Veg / Non-Veg, ingredients, cooking time

- Every food item has `food_type`: `VEG` or `NON_VEG` (also `is_veg: true/false`). The database
  enforces it (NOT NULL + CHECK constraint), so an item can never be left unclassified.
  Use it for the Veg / Non-Veg badge and the "Select item type" filter (`/items?food_type=VEG`).
- `ingredients` is a list of names only, e.g. `["Chicken", "Paratha", "Onion"]`. Quantities are not tracked.
- `avg_cooking_time_minutes` is on every food item and cart item. The cart returns
  `estimated_ready_minutes`, and an order returns `estimated_ready_at` / `estimated_ready_minutes`.
  Items are cooked in parallel, so the estimate is the slowest item's cooking time.

## Scarce, high-demand items (e.g. 1 portion left, many buyers)

Without protection, everyone sees the last portion as available, adds it to their cart,
and all but one person fail at checkout. Instead:

1. **Cart hold.** Adding an item, or changing its quantity, holds that stock for that
   customer for `CART_HOLD_MINUTES` (default 10). Other customers can't add or order held
   stock, and the holder is guaranteed to get it if they check out in time. Locking the
   stock row (`SELECT … FOR UPDATE`) means two people can't both hold the last portion.
2. **Fair-share limit.** At or below `LOW_STOCK_THRESHOLD` (default 5) portions, each customer
   can hold at most `LOW_STOCK_MAX_PER_CUSTOMER` (default 2), so one person can't take all of it.
3. **Advance notice on the items list.** Every item has `stock_status` + a ready-to-show `stock_message`:

   | `stock_status` | Meaning | Suggested UI |
   |---|---|---|
   | `IN_STOCK` | Plenty left | normal |
   | `LOW_STOCK` | Only a few left | yellow "Only a few left" tag |
   | `HIGH_DEMAND` | Few left **and** others have it in their cart, or it's one of today's most ordered | orange "Selling fast" tag + message |
   | `ALL_RESERVED` | Stock exists but it's all held in other carts; may free up | disable +1, show **Notify me** |
   | `OUT_OF_STOCK` | Sold out | disable +1, show **Notify me** |

   `max_order_quantity` is the most this customer can have now: disable "+1" at that number.
   `popular` marks the most ordered items of the last 24 h. Exact stock counts are never sent to
   customers, only to staff (`/staff/inventory`).
4. **Cart warnings.** Each cart line has `reservation_active`, `reserved_until`, `available` and a
   `message` such as "Held for you for 8 more min" or "Not enough left - reduce the quantity". When
   `can_checkout` is false, disable Checkout and show the item messages.
5. **Notifications.** `GET /notifications` (the app polls it) tells customers when:
   - an item they tapped **Notify me** on is available again (`BACK_IN_STOCK`)
   - an item in their cart sold out or not enough is left once their hold expired (`CART_ITEM_SOLD_OUT` / `CART_ITEM_LOW_STOCK`)
   - their order was placed, with the estimated ready time (`ORDER_PLACED`)

Settings (env vars): `CART_HOLD_MINUTES`, `LOW_STOCK_THRESHOLD`, `LOW_STOCK_MAX_PER_CUSTOMER`.

### Frontend (Android) changes to make

- **Item card:** Veg/Non-Veg badge from `food_type` (green ● Veg / red ▲ Non-Veg); "⏱ ~N min" from
  `avg_cooking_time_minutes`; a tag with `stock_message` when `stock_status` isn't `IN_STOCK`;
  disable "+1" when `in cart >= max_order_quantity`; a **Notify me** button instead of "+1" when
  `available` is false (`POST /notifications/stock-alerts`; the button shows as on when `notify_me` is true).
  Send the token on `GET /items` too, so the customer's own held items don't count as reserved.
- **View details:** show `ingredients` as a list and `description`.
- **Filters panel:** item type → `food_type`; category → `category_id`; price limit → `min_price` / `max_price`.
- **Cart:** under each item show `message` (red when `available` is false); show "Ready in ~N min"
  from `estimated_ready_minutes`; disable Checkout when `can_checkout` is false.
- **On a 409** from add / +1 / checkout, show `detail`. It already explains why, e.g.
  "Chicken Roll is running low: maximum 2 per customer".
- **Notifications:** poll `GET /notifications?unread_only=true` every ~30 s and when the app comes
  back to the foreground; show a bell badge from `unread_count` and a snackbar for new ones.
- **Order placed screen:** show `estimated_ready_minutes` / `estimated_ready_at`.

## Business rules implemented

- Passwords are hashed with Argon2; plaintext passwords are never stored.
- Students and faculty register and log in through their own endpoints; each login only accepts its own account type. Institute ID and username must be unique across everyone, and Password must equal Confirm Password. Staff accounts are seeded or created by an admin.
- Role-based access: a student token on `/staff/orders` returns **403 Forbidden**.
- An item becomes unavailable automatically when its quantity reaches 0.
- The cart and orders cannot exceed the available stock, and they can't use stock held in other customers' carts.
- Low-stock items are limited per customer; customers see a stock status, never the exact count.
- Every food item is either VEG or NON_VEG (enforced by the database).
- Placing an order runs as one transaction: lock the cart, lock the inventory rows
  (`SELECT … FOR UPDATE`), check stock, create the order and its items, reduce
  inventory, then clear the cart.
- Repeated "place order" taps cannot create duplicate orders, because the cart is locked and then cleared.
- Order items store the price at the time of the order.
- Customers can only see their own orders.

## Not in Demo 1 (planned)

Payment, pickup slots, the full order status flow (ACCEPTED → PREPARING → READY → COLLECTED),
pickup verification, cancellation, push notifications (FCM; in-app notifications are done),
feedback, reports, admin management.
