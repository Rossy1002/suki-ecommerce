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
- **Customer:** \`customer1\` / \`pass1234\` (Pre-loaded with ₱5,000.00 Suki Wallet Credits)
- **Seller:** \`seller1\` / \`sell1234\`
- **Admin:** \`admin\` / \`admin1234\`

## 3. Integrated APIs (Minimum 2 Distinct APIs)
1. **Suki Custom RESTful E-Commerce API (\`/api/\`):**
   - \`GET /api/products/\` — Catalog search & real-time license stock
   - \`POST /api/cart/checkout/\` — Atomic Suki Wallet deduction & seller payout
   - \`POST /api/orders/{id}/fulfill/\` — Email delivery dispatch via Django Mail API
   - \`GET /api/orders/sales_analytics/\` — Live seller revenue aggregation
2. **External Currency Exchange Rate API (\`/api/exchange-rates/\`):**
   - Fetches live PHP-to-USD/EUR/JPY rates with automatic offline fallback.
