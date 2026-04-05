# NOVA EATERY

NOVA EATERY is a QR code restaurant ordering system built with Flask and SQLite. It includes customer-facing pages for browsing the menu and placing orders, a kitchen dashboard for tracking preparation, and an admin panel for managing food items, payments, sales, and feedback.

## Features

- QR-style self-service ordering flow for customers
- Cart, checkout, and order placement experience
- Manual M-PESA payment confirmation workflow
- Kitchen dashboard for live order processing
- Admin dashboard for food management and sales reporting
- Customer order tracking and feedback submission
- CSV sales export for served orders

## Tech Stack

- Backend: Python, Flask, SQLite
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Authentication: Session-based login with PBKDF2 password hashing
- Payments: Manual M-PESA confirmation, no API integration

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000) after the server starts.

## Default Credentials

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin123` |
| Kitchen Staff | `kitchen` | `kitchen123` |

## Main Routes

| Page | URL |
| --- | --- |
| System Hub | `/` |
| Customer Landing | `/landing` |
| Menu | `/menu` |
| Cart | `/cart` |
| Checkout | `/checkout` |
| Order Tracking | `/my-orders` |
| Feedback | `/feedback` |
| Kitchen Login | `/kitchen-login` |
| Kitchen Dashboard | `/kitchen` |
| Admin Login | `/admin-login` |
| Admin Dashboard | `/admin-dashboard` |
| Food Management | `/admin-food` |
| Sales Report | `/admin-sales` |
| Payment Confirmation | `/admin-payment-confirmation` |
| Feedback Dashboard | `/admin-feedbacks` |

## Payment Flow

1. Customer browses the menu and adds items to the cart.
2. Customer proceeds to checkout and enters order details.
3. Customer sends payment through M-PESA to `0706444779`.
4. Customer places the order after confirming payment has been sent.
5. The order appears in the admin dashboard as pending payment.
6. Admin confirms payment and releases the order to the kitchen.
7. Kitchen staff update the order status from `Preparing` to `Ready` to `Served`.
8. Customer can check live progress on the order tracking page.

## Notes

- The app creates `.secret_key` automatically on first run for Flask sessions.
- The local SQLite database is stored in `database.db`.
- Sample users and starter menu items are seeded automatically when the database is first initialized.
- Payments are verified manually by admin staff before kitchen processing begins.

## Copyright

Copyright (c) 2026 TECH NOVA. All rights reserved.
