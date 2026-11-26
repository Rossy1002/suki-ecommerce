# Suki — Digital Product E-Commerce Platform (Canva Templates & E-Books)

A virtualized full-stack digital marketplace built with **Python (Django + Django REST Framework)** and **SQLite**, featuring **Suki Wallet** credit payments, real-time license inventory, and email-based digital delivery.

## 1. VM Provisioning & Startup Instructions
1. Ensure Python 3.10+ is installed inside the Ubuntu Linux VM.
2. Clone the repository and activate the isolated virtual environment:
   \`\`\`bash
   git clone https://github.com/Rossy1002/suki-ecommerce.git
   cd suki-ecommerce
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   \`\`\`
3. Run database migrations and start the server bound to all VM interfaces:
   \`\`\`bash
   python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   \`\`\`
4. Access the platform on the host browser via **\`http://127.0.0.1:8000\`** (with VM Port Forwarding `Host 8000 -> Guest 8000`).

## 2. Demo Accounts
- **Customer:** \`rossane.glovo@unc.edu.ph \` / \`suki1234\` (Pre-loaded with ₱5,000.00 Suki Wallet Credits)
- **Seller:** \`maya@suki.ph\` / \`aklat@suki.ph\` / \`sell1234\`

## APIs & Integrations Used

### 1. Internal Django REST API Endpoints
All internal endpoints are served under `/api/` and use session/CSRF token authentication:

| Endpoint | Methods | Purpose |
| :--- | :--- | :--- |
| `/api/login/` | `POST` | Authenticates existing buyers and sellers using username/email and password |
| `/api/register/` | `POST` | Registers new customer accounts and creates seller shops (supports `multipart/form-data` for shop logo & banner uploads) |
| `/api/profile/` & `/api/profile/{id}/` | `GET`, `PATCH` | Retrieves and updates user profiles, shop branding, addresses, and Suki Wallet top-up balances |
| `/api/shops/` | `GET` | Fetches verified creator storefronts and their published digital items |
| `/api/products/` & `/api/products/{id}/` | `GET`, `POST`, `PATCH`, `DELETE` | Manages digital product listings, drafts, pricing, stock licenses, file uploads, and multi-photo gallery ordering |
| `/api/cart/` & `/api/cart/{id}/` | `GET`, `POST`, `DELETE` | Adds, lists, and removes selected product variants in the customer's shopping cart |
| `/api/cart/checkout/` | `POST` | Processes selective shopping cart checkout and deducts credits from the Suki Wallet |
| `/api/wishlist/` & `/api/wishlist/{id}/` | `GET`, `POST`, `DELETE` | Saves and removes digital products in a customer's wishlist |
| `/api/orders/` | `GET` | Retrieves customer purchase history and seller fulfillment queues |
| `/api/orders/{id}/fulfill/` | `POST` | Marks an order as delivered and dispatches the digital download/Canva link to the buyer via email |
| `/api/reviews/` | `POST` | Submits star ratings and written customer reviews for purchased products |
| `/api/exchange-rates/` | `GET` | Fetches live PHP-to-USD conversion rates for displaying approximate USD pricing on product pages and wallets |

### 2. Third-Party Services & Authentication APIs
* **Google OAuth 2.0 (`django-allauth`):** Enables one-click social login and sign-up via `{% provider_login_url 'google' %}`.
* **Google Fonts API:** Loads the `Fraunces` and `Plus Jakarta Sans` typefaces (`fonts.googleapis.com`).
* **Django REST Framework Auth (`/api-auth/logout/`):** Handles session logout redirects.
```[cite: 22]