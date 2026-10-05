# DailyFundzBoost

> **Social Media Marketing Panel** - Boost your social media growth with followers, likes, views, and engagement for Instagram, TikTok, YouTube, Twitter & Facebook.

## 🚀 Features

- **SMM Panel**: Buy followers, likes, views, comments for all major platforms
- **Social Network**: Share posts, follow users, engage with content
- **Wallet System**: Deposit funds via OPay bank transfer
- **Multi-Currency**: Support for Nigerian Naira (₦) and US Dollar ($)
- **Admin Dashboard**: Manage users, orders, payments, and services

## Tech Stack

### Backend
- Python 3.12+
- Django 6
- Django REST Framework
- SimpleJWT for authentication
- SQLite (dev) / PostgreSQL (prod)

### Frontend
- Django templates and static assets

### Integrations
- **SMM Provider**: JustAnotherPanel API
- **Payments**: OPay Bank Transfer
- **Hosting**: Render.com

## 📦 Installation

### Local Setup
```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` (`Copy-Item .env.example .env` in PowerShell) and replace the development secret placeholder. The example enables `DEBUG` for local development. Then run:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 💳 Payment Details

**OPay Account**: 9070910294  
**Supported Currencies**: NGN (₦) and USD ($)

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (get JWT)
- `POST /api/auth/refresh/` - Refresh token
- `GET /api/auth/me/` - Current user info

### Wallet & Payments
- `GET /api/wallet/` - Get wallet balance
- `GET /api/deposits/` - List my deposits
- `POST /api/deposits/create/` - Create deposit request
- `GET /api/deposits/` - List my deposits
- `GET /api/wallet/transactions/` - Transaction history

### SMM Services
- `GET /api/platforms/` - List platforms
- `GET /api/services/` - List services
- `POST /api/orders/` - Create order
- `GET /api/orders/` - List my orders

## 📄 License

© 2026 DailyFundzBoost. All rights reserved.
