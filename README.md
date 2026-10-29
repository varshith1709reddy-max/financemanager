# Finance Manager

A lightweight, full-stack web application developed with Python (Flask) and SQLite to help track personal expenses, manage UPI/bank balances, set monthly spending limits, and save for financial goals.

---

## Project Overview

- **Project Title:** Finance Manager
- **Developer:** Varshith Reddy
- **Target Audience:** College Students
- **Domain:** Web Development / Full-Stack Information Systems
- **Technology Stack:**
  - **Backend:** Python 3, Flask, SQLite3 (with WAL mode & foreign keys)
  - **Frontend:** HTML5, CSS3 (Custom Responsive Design System), Vanilla JavaScript (ES6+)
  - **Data Visualizations:** HTML5 Canvas Chart Engine (Zero external CDN dependencies)
  - **Authentication:** PBKDF2 HMAC SHA-256 with per-user salt and session/bearer tokens

---

## System Architecture

```
personal-finance-manager/
├── app.py                      # Application entry point, routing, error handlers & demo seed
├── wsgi.py                     # Production/preview server runner (Waitress WSGI)
├── requirements.txt            # Python dependencies (Flask, pytest, waitress)
├── backend/
│   ├── database.py             # SQLite connection manager, schema initialization & WAL mode
│   ├── auth.py                 # PBKDF2 password hashing & token authentication
│   ├── routes_accounts.py      # Account balance ledger calculations & account CRUD
│   ├── routes_transactions.py  # Transaction CRUD, multi-criteria filtering & transfer logic
│   ├── routes_budgets.py       # Category budget limits, spent tracking & alert thresholds
│   ├── routes_goals.py         # Savings goals, progress tracking & goal contributions
│   ├── routes_dashboard.py     # Aggregated pocket money balance, monthly trends & KPIs
│   ├── routes_reports.py       # Cash flow analytics, category distributions & CSV export
│   ├── routes_categories.py    # College student categories (Canteen, Xerox, Travel, Books, etc.)
│   ├── seed_data.py            # Pre-configured student dataset (SBI, UPI, Cash)
│   └── setup_student_data.py   # Student database reset and population script
├── frontend/
│   ├── templates/
│   │   └── index.html          # Clean Single Page Application (SPA) layout
│   └── static/
│       ├── css/
│       │   └── styles.css      # Professional slate/navy design system (offline compatible)
│       └── js/
│           ├── api.js          # REST API client with Bearer token & session management
│           ├── charts.js       # Standalone HTML5 Canvas charts (Double Bar, Donut, Line)
│           └── app.js          # Main application state and UI event controllers
└── tests/
    ├── conftest.py             # Pytest fixtures and isolated SQLite test harness
    ├── test_auth.py            # Authentication, registration, login & profile tests
    ├── test_accounts.py        # Account balances & CRUD tests
    ├── test_transactions.py    # Transaction CRUD, transfers & automatic balance sync tests
    ├── test_budgets.py         # Budget limits, spent calculations & alert flags tests
    ├── test_goals.py           # Savings goals, contributions & completion tests
    ├── test_dashboard_reports.py # Dashboard KPIs, cash flow analytics & CSV export tests
    └── test_live_server.py     # Live HTTP end-to-end verification script
```

---

## Core Features

| Module | Features & Capabilities |
|---|---|
| **Student Authentication** | Secure registration and login using PBKDF2 HMAC SHA-256 with per-user salt. Instant student demo login for quick grading. |
| **Pocket Money Dashboard** | Total student balance across accounts, monthly pocket money received, expenses spent, net savings, and active budget alerts. |
| **Accounts & Wallets** | Manage student accounts: SBI Student Account, GPay / UPI, and Cash in Pocket with atomic balance recalculations. |
| **Expense & Income Ledger** | Log canteen snacks, xerox/printing, books, recharge, bus/metro travel, or freelance tutoring income with date, category, and account filters. |
| **Account Transfers** | Atomic transfer between bank accounts, UPI wallets, and cash with validation and rollback safety. |
| **Student Monthly Budgets** | Set monthly spending limits per category (e.g., ₹2,500 for Canteen, ₹800 for Travel) with alert indicators when spending exceeds 80%. |
| **College Savings Goals** | Track savings milestones (e.g., Semester Exam Fees, Placement Course, Tech Gadgets) with progress bars and direct deposits. |
| **Reports & CSV Export** | 6-month cash flow trends, category breakdown charts, and one-click transaction export to CSV. |

---

## Quickstart & Execution Guide

### 1. Requirements
- Python 3.10+ installed
- Terminal / PowerShell

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Web Application
```bash
python app.py
```
Or with Waitress WSGI:
```bash
python wsgi.py
```
Open **`http://localhost:5000`** in any web browser.

### 4. Logging In
- **Existing Student Account:**
  - Username: `varshhh`
  - Password: `password123`
- **Or Quick Demo Account:**
  - Click **"Demo Student"** button on the sign-in screen to instantly load the pre-populated demo ledger (`demo` / `password123`).
- **Or Register a New Account:**
  - Click **"Create Account"** to register your own account.

---

## Running Automated Tests

Run the complete test suite (26 automated tests covering all backend modules, authentication, transactions, and calculations):

```bash
python -m pytest tests --rootdir=. -v
```

All 26 tests run against an isolated SQLite test database and pass with 100% coverage of core endpoints.

---

## REST API Endpoints

- `POST /api/auth/register` - Student registration
- `POST /api/auth/login` - Student sign-in
- `GET  /api/auth/me` - Profile information
- `GET  /api/accounts` - List accounts and balances
- `POST /api/accounts` - Create new wallet or bank account
- `GET  /api/transactions` - Filtered transactions list
- `POST /api/transactions` - Add expense or income
- `POST /api/transactions/transfer` - Transfer money between accounts
- `GET  /api/budgets?month=YYYY-MM` - View monthly category budgets
- `POST /api/budgets` - Set category budget limit
- `GET  /api/goals` - View savings goals and progress
- `POST /api/goals/<id>/contribute` - Add money to savings goal
- `GET  /api/dashboard/summary` - Aggregate metrics for dashboard
- `GET  /api/reports/export` - Export transactions as CSV
