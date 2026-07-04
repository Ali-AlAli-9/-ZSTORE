# ZSTORE — E-Commerce Platform

Full-stack e-commerce with Django REST Framework (Python 3.14 + Django 6.0) backend and React 19 + Vite 8 + Tailwind CSS v4 frontend.

## Features

- **User Authentication** — Register, login, logout with JWT (access token in memory, refresh token in httpOnly cookie with rotation + blacklist)
- **Email Verification** — Required before checkout. Token-based verification with resend and email update support. Throttled (3/min per user).
- **Product Catalog** — CRUD for admin, search by name/description, filter by price, sort by price/date/name, paginated (20/page).
- **Shopping Cart** — Add/update items with SET semantics (`quantity: 0` removes). No stock limit — users can request any quantity.
- **Order Management** — Full state machine (pending → confirmed → shipped → delivered, with cancel). Stock decremented on checkout (can go negative as oversell indicator), restored on cancel.
- **Payment Selection** — COD (Cash on Delivery, active) / CARD (UI ready, coming soon).
- **Admin Dashboard** — Overview stats, order status distribution, best sellers, low stock alerts, full order management with status transitions and archiving, product CRUD.
- **Security** — Rate limiting (login 10/min, register 10/hr, email 3/min, anon 60/hr, user 10000/hr), CORS, env-based secrets, stock handled with `select_for_update()` to prevent race conditions.
- **API Documentation** — OpenAPI schema at `/api/schema/`, Swagger UI at `/api/docs/` via `drf-spectacular`.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.14 + Django 6.0.3 | Web framework |
| Django REST Framework 3.16 | API framework |
| PostgreSQL 18 | Database |
| SimpleJWT 5.5 | JWT auth (cookie-based refresh) |
| django-filter 25 | Advanced filtering |
| drf-spectacular 0.29 | OpenAPI/Swagger docs |
| python-decouple 3.8 | Environment config |
| waitress 3.0 | Production WSGI server |
| whitenoise 6.12 | Static file serving |
| React 19 | Frontend framework |
| Vite 8 | Build tool |
| Tailwind CSS v4 | Styling |
| React Router DOM 7 | Client-side routing |
| Axios 1 | HTTP client |
| TypeScript 6 | Strict mode |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL 16+ (or SQLite for quick dev)

### Backend Setup

```bash
# Clone and enter the project
cd ecommerce

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in your values
cp .env.example .env

# Run migrations
python manage.py migrate

# Create a superuser (admin)
python manage.py createsuperuser

# (Optional) Seed demo products
python manage.py seed_products

# Start Django
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` and proxies API requests to Django on port 8000.

### Default Credentials (after seeding)

- **Admin:** `zoro1` / `zoro123456`

## Environment Variables (.env)

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://postgres:password@localhost:5432/ecommerce_db
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=ZSTORE <your-email@gmail.com>
FRONTEND_URL=http://localhost:5173
DB_PASSWORD=your-db-password
```

`.env` is in `.gitignore` — never commit it.

## Order State Machine

```
pending ──► confirmed ──► shipped ──► delivered
  │                            │
  └──► cancelled (from pending or confirmed only)
```

Enforced at both the model (`clean()`) and serializer (`validate_status()`) level. Stock is decremented on checkout and restored on cancel.

## API Endpoints

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/users/register/` | None | Register (throttled 10/hr) |
| POST | `/users/login/` | None | Login (throttled 10/min) |
| POST | `/users/logout/` | JWT | Logout + blacklist refresh |
| POST | `/users/token/refresh/` | Cookie | Refresh access token |
| GET | `/users/me/` | JWT | Current user profile |
| GET | `/users/` | Admin | List all users |
| GET | `/users/verify/<uidb64>/<token>/` | None | Verify email |
| POST | `/users/resend-verification/` | JWT | Resend verification (throttled 3/min) |
| POST | `/users/update-email/` | JWT | Change email (throttled 3/min) |

### Products

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/products/` | None | List (paginated, 20/page) — public: no `stock` field, admin: includes `stock` |
| GET | `/products/{id}/` | None | Product detail — stock visible only to admin |
| POST | `/products/` | Admin | Create |
| PATCH | `/products/{id}/` | Admin | Update |
| DELETE | `/products/{id}/` | Admin | Delete |

**Query params:** `search`, `price__gte`, `price__lte`, `price__gt`, `price__lt`, `ordering`

### Cart

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/cart/` | JWT | View cart items |
| POST | `/cart/` | JWT | Add/update item (SET semantics, `quantity: 0` removes) |

### Orders

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/orders/` | JWT | List user's orders |
| GET | `/orders/{id}/` | JWT | Order details |
| PATCH | `/orders/{id}/` | JWT | Set payment method |
| POST | `/orders/checkout/` | JWT | Place order (email must be verified) |
| POST | `/orders/{id}/cancel/` | JWT | Cancel pending order |
| GET | `/orders/admin-orders/` | Admin | List all orders (`?archived=true`) |
| PATCH | `/orders/admin-orders/{id}/` | Admin | Update status, archive |

### Dashboard (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/overview/` | Stats, order counts, low stock products |
| GET | `/dashboard/best-sellers/` | Top products by sales (`?limit=N`) |

### API Docs

| URL | Description |
|-----|-------------|
| `/api/schema/` | OpenAPI schema (YAML) |
| `/api/docs/` | Swagger UI |

## Frontend Structure

```
frontend/src/
├── api/
│   └── axios.ts               # Axios with JWT interceptor + auto-refresh
├── components/
│   ├── AdminRoute.tsx          # Guard — is_staff only
│   ├── ConfirmDialog.tsx       # Reusable confirmation modal
│   ├── ErrorBoundary.tsx       # Runtime error catch with Reload fallback
│   ├── Navbar.tsx              # Nav with auth state + dark mode toggle + admin link
│   ├── ProductCard.tsx         # Product grid card
│   └── ProtectedRoute.tsx      # Guard — authenticated only
├── context/
│   └── AuthContext.tsx         # Auth state + login/register/logout/refreshUser
├── pages/
│   ├── Home.tsx               # Product listing
│   ├── ProductDetail.tsx      # Product page with add-to-cart
│   ├── Cart.tsx               # Cart with quantity controls
│   ├── Checkout.tsx           # Shipping form + email verification
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Orders.tsx             # Order history with cancel + payment
│   ├── PaymentSelection.tsx   # COD/CARD selection
│   ├── AdminDashboard.tsx     # Overview / Orders / Products tabs
│   ├── AdminProducts.tsx      # Product CRUD table
│   ├── VerifyPending.tsx      # "Check your email" page
│   └── VerifyEmail.tsx        # Verification handler
├── types.ts                   # All TypeScript interfaces
├── App.tsx                    # Routes with guards
└── main.tsx                   # Entry point
```

## Testing

```bash
# Run all 98 tests
python manage.py test

# By app
python manage.py test users      # 17 tests
python manage.py test products   # 10 tests
python manage.py test cart       # 6 tests
python manage.py test orders     # 38 tests
python manage.py test dashboard  # 27 tests
```

## Docker

```bash
# Start PostgreSQL + Django
docker compose up --build
```

The Django app runs on port 8000. Frontend still needs `cd frontend && npm run dev` separately.

## Project Structure

```
ecommerce/
├── cart/                     # Shopping cart (Cart, CartItem models)
├── dashboard/                # Admin analytics / overview
├── ecommerce/                # Django settings, URLs, WSGI
├── frontend/                 # React + Vite + Tailwind
├── orders/                   # Order processing, state machine, payment
├── products/                 # Product catalog
├── users/                    # Auth, email verification, throttles
├── media/                    # Uploaded product images
├── staticfiles/              # Collected static assets
├── .env                      # Environment variables (gitignored)
├── .env.example              # Template for .env
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT
"# -ZSTORE" 
"# -ZSTORE" 
"# -ZSTORE" 
