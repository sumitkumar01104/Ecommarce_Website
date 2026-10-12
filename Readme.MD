# ShopKart: Django E-commerce

🔗 **Live demo:** https://ecommarce-website-l7cr.onrender.com
_(Hosted on Render's free plan, so the first load after a period of inactivity can take 30-60 seconds.)_

**Demo account:** `demo@example.com` · password `Demo@12345`
_(The live site runs in **demo mode** because Render's free plan has no Celery worker: new sign-ups are verified automatically and emails are turned off. Run it locally or with Docker for the full email verification and order-invoice flow.)_

A full-stack e-commerce application built with Django. It covers the complete shopping flow: browse products, add to cart (even as a guest), verify your email, place a Cash-on-Delivery order, and receive a PDF invoice by email. Email sending runs in the background with Celery and Redis.

## Features

- **Catalogue:** categories, product pages with multiple images, colour and size variants with price add-ons
- **Cart:** works for guests (session based) and logged-in users; the guest cart is merged into the user's cart on login
- **Authentication:** email-based register / login with **email verification** (activation link sent through Celery)
- **Checkout:** delivery details validation (Indian mobile number and 6-digit pincode), Cash on Delivery
- **Orders:** order history, order success page, price snapshot stored per order item
- **PDF invoice:** generated with ReportLab and attached to the order confirmation email
- **REST API:** register, login, logout, profile, JWT tokens with refresh and blacklist, Swagger / ReDoc docs
- **Docker:** `docker compose` setup for web, PostgreSQL, Redis and the Celery worker
- **Deployment:** Dockerized and deployed on Render, with product images stored on Cloudinary

## Tech stack

Python, Django, Django REST Framework, SimpleJWT, drf-spectacular, Celery, Redis, PostgreSQL, ReportLab, Docker, Gunicorn, WhiteNoise, Cloudinary, Render.

## Project structure

```
ecommarce/            project settings, urls, celery app
Account/              register / login pages, REST API, Profile model
verificationsystem/   email activation (Celery task + activation view)
Products/             Category, Product, variants, images
Cart/                 session + user cart, merge on login
Orders/               checkout, orders, invoice PDF, confirmation email task
Home/                 home page and category listing
templates/            HTML templates
```

## Getting started (local)

### 1. Requirements

- Python 3.12+
- PostgreSQL
- Redis (easiest through Docker: `docker run -p 6379:6379 redis:7-alpine`)

### 2. Install

```bash
git clone <your-repo-url>
cd Ecommarce_Fixed

python -m venv cenv
# Windows
.\cenv\Scripts\activate
# macOS / Linux
source cenv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Fill in `.env`:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail address and a Gmail **App Password** (needs 2-step verification) |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis URLs |
| `DEMO_MODE` | `False` (default) = full email flow. `True` = auto-verify users and skip emails, for hosting without a Celery worker |
| `SITE_NAME`, `DELIVERY_DAYS`, `SITE_DOMAIN` | Used in emails and invoices |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Cloudinary credentials for uploaded product images |

Never commit `.env`.

### 4. Database and run

Create the PostgreSQL database first, then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a **second terminal** (same virtual environment), start the Celery worker. Without it, verification and order emails are not sent.

```bash
# Windows needs --pool=solo
celery -A ecommarce worker -l info --pool=solo

# macOS / Linux
celery -A ecommarce worker -l info
```

Open http://127.0.0.1:8000/. Add categories and products from the admin panel at `/admin/`, or load sample data with `python manage.py seed_products`.

## Run with Docker

```bash
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

This starts PostgreSQL, Redis, the Django app (migrations run on start) and the Celery worker. The app is available at http://127.0.0.1:8000/.

## Deployment (Render)

The app is deployed as a Docker web service on Render with a managed PostgreSQL database. Configuration is done through environment variables (see `.env.example`). Set `DEMO_MODE=True` on Render's free plan, since there is no Celery worker there. Static files are served by WhiteNoise and uploaded images are stored on Cloudinary, because Render's disk is not persistent.

## Main routes

| Route | Description |
| --- | --- |
| `/` | Home, all products |
| `/category/<slug>/` | Products by category |
| `/product/<slug>/` | Product details |
| `/cart/` | Cart |
| `/orders/checkout/` | Checkout (login required) |
| `/orders/my-orders/` | Order history |
| `/account/register/`, `/account/login/`, `/account/logout/` | Auth pages |
| `/account/activate/<token>/` | Email activation link |

## REST API

Interactive docs: `/api/docs/` (Swagger) and `/api/redoc/`.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/account/api/register/` | POST | Create an account (sends verification email) |
| `/account/api/login/` | POST | Login with email and password, returns JWT tokens |
| `/api/token/` | POST | Obtain JWT pair (blocked until the email is verified) |
| `/api/token/refresh/` | POST | Refresh access token |
| `/account/api/logout/` | POST | Blacklist the refresh token |
| `/account/api/profile/` | GET, PUT, PATCH | Current user's profile |

Send the access token as `Authorization: Bearer <token>`.

## How the email flow works

1. User registers; a `Profile` is created by a `post_save` signal with a unique activation token.
2. A Celery task sends the activation link by email (retries up to 3 times on failure).
3. The user opens the link, the profile is marked verified, and login is allowed.
4. After checkout, another Celery task builds the PDF invoice and emails the order confirmation.

## Screenshots

_Add screenshots of the home page, product page, cart, checkout and invoice here._

## Roadmap

- Resend verification email
- Online payments
- Automated tests
- Email delivery and Celery worker on the live deployment

## Author

Sumit: [github.com/sumitkumar01104](https://github.com/sumitkumar01104)
