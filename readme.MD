# 🍽️ Restaurant ERP Management System
### System Documentation — For Project Manager & Client
**Version:** 1.0  
**Date:** April 2026  
**Status:** In Development

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Modules](#2-system-modules)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [System Flow Diagrams](#4-system-flow-diagrams)
5. [Module Breakdown](#5-module-breakdown)
6. [Technical Architecture](#6-technical-architecture)
7. [Development Roadmap](#7-development-roadmap)
8. [API Overview](#8-api-overview)

---

## 1. Project Overview

### General Objective
A modern, integrated Restaurant ERP system that synchronizes **sales**, **inventory**, **human resources**, and **asset management** into a single unified platform. The system is designed to support multi-branch restaurant operations including Cafe, Restaurant, and Bar sections.

### Key Goals
- Streamline daily restaurant operations from table to kitchen to payment
- Automate inventory deduction based on recipes
- Provide real-time reporting and financial insights
- Support offline operations via local server
- Enable QR-based digital menus and payments
- Centralize HR, payroll, and asset management

---

## 2. System Modules

| # | Module | Description |
|---|---|---|
| 1 | **Sales & POS** | Multi-section point of sale, table management, KOT/BOT |
| 2 | **QR Services** | QR digital menu and QR payment integration |
| 3 | **Inventory & Recipe** | Auto stock deduction, alerts, wastage tracking |
| 4 | **HR & Payroll** | Employee records, attendance, salary calculation |
| 5 | **Asset Management** | QR-tracked assets, depreciation, maintenance |
| 6 | **Financial Reporting** | Profit & Loss, expense tracking, daily reports |
| 7 | **Technical Infrastructure** | Offline mode, RBAC security, auto backups |

---

## 3. User Roles & Permissions

### Role-Based Access Control (RBAC)

| Role            | POS  | Menu | Tables | Inventory | HR | Reports | Assets | Admin |
|-----------------|------|------|--------|-----------|----|---------|--------|-------|
| **Admin**       | ✅  | ✅   | ✅    | ✅        | ✅ | ✅     | ✅    | ✅    |
| **Manager**     | ✅  | ✅   | ✅    | ✅        | ✅ | ✅     | ✅    | ❌    |
| **Cashier**     | ✅  | 👁️   | 👁️    | ❌        | ❌ | 👁️     | ❌    | ❌    |
| **Waiter**      | ✅  | 👁️   | ✅    | ❌        | ❌ | ❌     | ❌    | ❌    |
| **Chef**        | 👁️  | 👁️   | ❌    | ❌        | ❌ | ❌     | ❌    | ❌    |
| **Bartender**   | 👁️  | 👁️   | ❌    | ❌        | ❌ | ❌     | ❌    | ❌    |
| **HR Officer**  | ❌  | ❌   | ❌    | ❌        | ✅ | 👁️     | ❌    | ❌    |

> ✅ Full Access  👁️ View Only  ❌ No Access

### Role Descriptions

**Admin**
- Full system access across all branches
- Creates and manages user accounts
- Configures system settings and backups

**Manager**
- Oversees branch operations
- Manages menu, staff, and inventory
- Views financial reports and analytics

**Cashier**
- Handles payments and invoice generation
- Processes bills via cash, bank transfer, or digital wallets
- Views table status for billing purposes

**Waiter**
- Takes and modifies customer orders
- Manages table status (available/occupied)
- Sends KOT to kitchen

**Chef**
- Views Kitchen Order Tickets (KOT)
- Updates order preparation status
- Cannot access financial or HR data

**Bartender**
- Views Bar Order Tickets (BOT)
- Updates drink preparation status

**HR Officer**
- Manages employee records and attendance
- Processes payroll and generates payslips

---

## 4. System Flow Diagrams

### 4.1 Reservation Flow

```
CUSTOMER
   │
   ▼
Customer contacts restaurant (phone/walk-in)
   │
   ▼
RECEPTIONIST searches available tables
   │ (filters by date, time, capacity)
   ▼
Table found? ──── NO ──► Inform customer, suggest alternative time
   │
  YES
   │
   ▼
Receptionist creates reservation
   │
   ▼
System sends CONFIRMATION NOTIFICATION to customer
   │
   ▼
Customer arrives on reservation date
   │
   ▼
Receptionist CHECK-IN → Table status: RESERVED → OCCUPIED
   │
   ▼
Waiter assigned to table
```

---

### 4.2 Walk-in Customer Flow

```
CUSTOMER walks in
   │
   ▼
Receptionist checks AVAILABLE TABLES (real-time)
   │
   ▼
Table available? ──── NO ──► Add to waitlist or suggest return time
   │
  YES
   │
   ▼
Customer seated → Table status: AVAILABLE → OCCUPIED
   │
   ▼
Waiter assigned to table
```

---

### 4.3 Order Flow (POS)

```
WAITER opens table on POS
   │
   ▼
Waiter takes order from customer
   │
   ▼
Waiter enters meal items per seat (food & drinks)
   │
   ├──────────────────────────────────────┐
   ▼                                      ▼
FOOD items → KOT sent to Kitchen    DRINK items → BOT sent to Bar
   │                                      │
   ▼                                      ▼
CHEF views KOT on screen/printer    BARTENDER views BOT
   │                                      │
   ▼                                      ▼
Chef prepares food                  Bartender prepares drinks
   │                                      │
   ▼                                      ▼
Chef marks order READY              Bartender marks order READY
   │                                      │
   └──────────────┬───────────────────────┘
                  ▼
         WAITER delivers to table
                  │
                  ▼
         Customer finishes meal
```

---

### 4.4 Payment Flow

```
CUSTOMER requests bill
   │
   ▼
WAITER requests bill generation
   │
   ▼
CASHIER generates invoice
   │ (all meal items + quantities + prices)
   ▼
Customer selects payment method:
   │
   ├──► CASH → Cashier processes cash payment
   │
   ├──► BANK TRANSFER → System records transfer
   │
   ├──► DIGITAL WALLET → QR code displayed for payment
   │        │
   │        └── Telebirr / Banking App scans QR
   │
   └──► CREDIT CARD → Card terminal processes payment
   │
   ▼
Receipt printed / sent digitally
   │
   ▼
Table status: OCCUPIED → CLEANING → AVAILABLE
```

---

### 4.5 Inventory Auto-Deduction Flow

```
ORDER submitted by waiter
   │
   ▼
System checks RECIPE for each menu item
   │ (e.g., Pasta = 200g flour + 100ml oil + 150g meat)
   ▼
Ingredients AUTO-DEDUCTED from stock
   │
   ▼
Check stock levels:
   │
   ├── Stock LOW? ──► ALERT sent to Manager
   │
   ├── Item EXPIRED? ──► Wastage log created + Manager alerted
   │
   └── Stock OK? ──► Continue normally
```

---

### 4.6 Reservation Cancellation Flow

```
CUSTOMER requests cancellation
   │
   ▼
Receptionist finds reservation in system
   │
   ▼
Receptionist cancels reservation
   │
   ▼
Table status: RESERVED → AVAILABLE
   │
   ▼
System sends CANCELLATION NOTIFICATION to customer
```

---

### 4.7 HR & Payroll Flow

```
EMPLOYEE clocks in
   │
   ▼
Attendance recorded (timestamp)
   │
   ▼
Employee works shift
   │
   ▼
Employee clocks out → Hours calculated
   │
   ▼
End of month:
   │
   ▼
System calculates:
   ├── Base Salary
   ├── Overtime (OT) hours × rate
   └── Deductions (taxes, absences)
   │
   ▼
Payslip generated automatically
   │
   ▼
Payment processed → Record stored
```

---

### 4.8 Asset Management Flow

```
NEW ASSET purchased (furniture, equipment, electronics)
   │
   ▼
Asset registered in system
   │
   ▼
QR code generated and attached to asset
   │
   ▼
Monthly: Depreciation auto-calculated
   │
   ▼
Maintenance schedule set
   │
   ▼
Reminder sent when maintenance due
   │
   ▼
Maintenance logged → Next schedule updated
```

---

## 5. Module Breakdown

### 5.1 Sales & POS Module

**Features:**
- Multi-section POS interfaces (Cafe, Restaurant, Bar)
- Real-time table status monitoring (Available / Occupied / Reserved / Cleaning)
- Kitchen Order Tickets (KOT) sent to kitchen display/printer
- Bar Order Tickets (BOT) sent to bar display/printer
- Invoice generation with itemized billing
- Multiple payment method support

**Key Screens:**
- Table map view (real-time status)
- Order entry screen (per seat)
- KOT/BOT display screen
- Payment & invoice screen

---

### 5.2 QR Services Module

**Features:**
- **QR Menu:** Customers scan table QR code to view digital menu on their phone — no physical menu needed
- **QR Payment:** Integrated QR codes for Telebirr and banking apps for seamless contactless payment

**Flow:**
```
Customer scans QR code on table
   │
   ▼
Digital menu loads on their phone (no app needed)
   │
   ▼
Customer browses menu, places order (optional self-ordering)
   │
   ▼
For payment: QR code displayed at checkout
   │
   ▼
Customer scans with Telebirr / banking app → Payment confirmed
```

---

### 5.3 Inventory & Recipe Management Module

**Features:**
- Ingredient stock management per branch
- Recipe builder (links menu items to ingredients with exact quantities)
- Auto-deduction on every order
- Low-stock threshold alerts
- Expiration date tracking
- Wastage/spoilage logging

**Example Recipe:**
```
Menu Item: Beef Burger
Recipe:
  - Beef patty:     200g
  - Burger bun:     1 piece
  - Lettuce:        30g
  - Tomato:         50g
  - Cooking oil:    10ml
  - Cheese:         25g
```
When 1 Beef Burger is sold → All above quantities auto-deducted from stock.

---

### 5.4 Human Resources & Payroll Module

**Features:**
- Centralized employee database (personal info, role, branch, contract)
- Clock-in / Clock-out attendance tracking
- Overtime calculation
- Automated payroll with salary, OT, and deductions
- Payslip generation and history

---

### 5.5 Fixed Asset Management Module

**Features:**
- Asset registration with category (furniture, machinery, electronics)
- QR code labels for each asset (scan to view details)
- Automated monthly depreciation calculation
- Maintenance schedule and reminders
- Asset history log (repairs, transfers)

---

### 5.6 Financial Reporting Module

**Features:**
- **Daily Reports:** Sales summary, top-selling items, payment method breakdown
- **Monthly Reports:** Revenue, expenses, payroll costs, net profit
- **Annual Reports:** Full P&L statement, asset value, trends
- **Expense Tracking:** Rent, utilities, procurement, maintenance costs

**Sample Report Structure:**
```
Daily Financial Summary - [Branch Name] - [Date]
─────────────────────────────────────────────────
Total Sales:              ETB 45,200
  ├── Cafe Section:       ETB 12,400
  ├── Restaurant:         ETB 28,500
  └── Bar:                ETB  4,300

Payment Methods:
  ├── Cash:               ETB 18,000
  ├── Bank Transfer:      ETB 15,200
  └── Digital (Telebirr): ETB 12,000

Total Expenses:           ETB 22,100
─────────────────────────────────────
Net Profit:               ETB 23,100
```

---

## 6. Technical Architecture

### Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Django + Django REST Framework | Core API and business logic |
| **Frontend** | React.js | Web-based dashboard UI |
| **Database** | PostgreSQL | Primary data store |
| **Local Server** | Django on LAN | Offline mode support |
| **QR Codes** | Python `qrcode` library | Menu & asset QR generation |
| **Printing** | ESC/POS integration | KOT/BOT/receipt printing |
| **Auth** | Django RBAC + JWT | Role-based access control |
| **Background Tasks** | Celery + Redis | Alerts, notifications, backups |
| **Notifications** | Email / SMS / In-app | Reservation alerts, low-stock |

---

### Django App Structure

```
restaurant_erp/                    ← Main Django project
│
├── accounts/                      ← Users, roles, branches, RBAC
├── pos/                           ← POS, orders, KOT/BOT
├── tables/                        ← Table management, seating
├── menu/                          ← Menu sections, items, QR menu
├── inventory/                     ← Stock, recipes, wastage
├── hr/                            ← Employees, attendance, payroll
├── assets/                        ← Fixed assets, depreciation
├── finance/                       ← Reports, expenses, P&L
├── notifications/                 ← Alerts, reservation reminders
└── core/                          ← Settings, backup, offline config
```

---

### Database Schema (Simplified)

```
Branch
  └── has many → Users (Employees)
  └── has one  → Menu
  └── has many → Tables
  └── has many → SeatingArrangements

Menu
  └── has many → MenuSections
        └── has many → MenuItems
                └── has many → RecipeIngredients

Table
  └── has many → TableSeats
  └── has many → Reservations
  └── has many → Orders

Order
  └── belongs to → Table
  └── belongs to → Waiter (User)
  └── belongs to → Chef (User)
  └── has many  → Meals (per seat)
        └── has many → MealItems (menu items)

Bill
  └── belongs to → Order
  └── has many  → BillItems
  └── has one   → Payment

Employee (User)
  └── has many → AttendanceRecords
  └── has one  → PayrollRecord (monthly)

Asset
  └── has one  → QR Code
  └── has many → DepreciationRecords
  └── has many → MaintenanceLogs
```

---

### Offline Mode

The system supports operation on a **Local Area Network (LAN)** when internet connectivity is unavailable:

- Django server runs on a local machine
- All POS, order, and payment operations work offline
- Data syncs automatically when internet is restored
- Daily backups stored locally and to cloud when connected

---

## 7. Development Roadmap

### Phase 1 — Foundation (Weeks 1–3)
- [x] Project setup & configuration
- [x] Accounts & RBAC module
- [x] Menu module
- [x] Tables module

### Phase 2 — Core Operations (Weeks 4–6)
- [ ] POS & Orders module (KOT/BOT)
- [ ] Reservations module
- [ ] Payment & invoicing module

### Phase 3 — Inventory & QR (Weeks 7–9)
- [ ] Inventory & recipe management
- [ ] Auto-deduction engine
- [ ] QR menu & QR payment integration

### Phase 4 — HR & Assets (Weeks 10–12)
- [ ] HR & attendance module
- [ ] Payroll automation
- [ ] Fixed asset management

### Phase 5 — Reporting & Polish (Weeks 13–15)
- [ ] Financial reporting & P&L
- [ ] Expense tracking
- [ ] Dashboard & analytics

### Phase 6 — Technical Hardening (Weeks 16–17)
- [ ] Offline mode & LAN server setup
- [ ] Automated daily backups
- [ ] Security audit & RBAC testing
- [ ] Performance optimization

### Phase 7 — Testing & Launch (Weeks 18–20)
- [ ] Full system testing (UAT)
- [ ] Staff training
- [ ] Pilot launch (one branch)
- [ ] Full rollout

---

## 8. API Overview

### Base URL
```
https://api.restauranterp.com/api/
```
or for local server:
```
http://192.168.1.x:8000/api/
```

### Core Endpoints

#### Accounts
| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/accounts/login/` | User login | Public |
| POST | `/accounts/logout/` | User logout | All |
| POST | `/accounts/register/` | Create user | Admin |
| GET | `/accounts/users/` | List users | Manager+ |
| GET/PUT | `/accounts/users/{id}/` | User detail | Manager+ |
| GET/POST | `/accounts/branches/` | List/create branches | Admin |

#### Menu
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/menu/` | Get branch menu | All staff |
| GET | `/menu/public/{branch_id}/` | Public QR menu | Public |
| GET/POST | `/menu/sections/` | Menu sections | Manager+ |
| GET/PUT/DELETE | `/menu/sections/{id}/` | Section detail | Manager+ |
| GET/POST | `/menu/items/` | Menu items | Manager+ |
| GET/PUT/DELETE | `/menu/items/{id}/` | Item detail | Manager+ |

#### Tables
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET/POST | `/tables/` | List/create tables | Waiter+ |
| GET/PUT/DELETE | `/tables/{id}/` | Table detail | Manager+ |
| GET | `/tables/available/` | Available tables | All staff |
| PATCH | `/tables/{id}/status/` | Update table status | Waiter+ |
| POST | `/tables/{id}/qr/` | Generate table QR | Manager+ |
| GET/POST | `/tables/arrangements/` | Seating arrangements | Manager+ |

> Additional endpoints for POS, Inventory, HR, Assets, and Finance to be added in subsequent phases.

---

## 9. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Performance** | API response time < 500ms under normal load |
| **Uptime** | 99.5% availability (LAN fallback for internet outages) |
| **Security** | RBAC, encrypted passwords, HTTPS, JWT tokens |
| **Backup** | Automated daily backups, 30-day retention |
| **Scalability** | Supports multiple branches from single deployment |
| **Compatibility** | Works on desktop browsers, tablets, mobile |
| **Printing** | Compatible with standard ESC/POS thermal printers |

---

*Document prepared by the development team. Last updated: April 2026.*