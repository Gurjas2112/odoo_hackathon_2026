# 🚚 TransitOps: Smart Transport Operations Platform

<div align="center">

[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-blueviolet.svg?style=for-the-badge&logo=odoo)](https://www.odoo.com)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg?style=for-the-badge&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%20%7C%2016-blue.svg?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)
[![Framework](https://img.shields.io/badge/UI--Framework-OWL--19-emerald.svg?style=for-the-badge)](https://github.com/odoo/owl)
[![License](https://img.shields.io/badge/License-LGPL--3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/lgpl-3.0.html)

**An enterprise-grade fleet logistics, dispatch, and financial tracking system designed to eliminate spreadsheet chaos and automate compliance in real-time.**

<a href="https://drive.google.com/drive/folders/1Xi77KDxRjo7IMGa5yuB7m1uAiOmzGyRr?usp=sharing" target="_blank">
  <img src="https://img.shields.io/badge/Google_Drive-Video_Demo_🎞️-red?style=for-the-badge&logo=googledrive&logoColor=white" alt="Video Demo" />
</a>

<br/><br/>

[Explore Features](#-core-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Security & RBAC](#-security--rbac)

</div>

---

## 📋 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Solution Overview](#-solution-overview)
3. [Visual Walkthrough](#-visual-walkthrough)
4. [Architecture](#-architecture)
5. [Business Rules & Robustness Matrix](#-business-rules--robustness-matrix)
6. [Technical Highlights & Odoo 19 Best Practices](#-technical-highlights--odoo-19-best-practices)
7. [Core Features](#-core-features)
8. [Tech Stack](#-tech-stack)
9. [Module Structure](#-module-structure)
10. [Security & RBAC](#-security--rbac)
11. [Team & Roles](#-team--roles)
12. [Quick Start](#-quick-start)
13. [Automated Verification (Test Suite)](#-automated-verification-test-suite)

---

## 🔍 Problem Statement

In modern logistics and transport operations, organizations face severe operational hurdles when managing fleets manually:
- **Scheduling Conflicts & Double Bookings:** Dispatching a vehicle or driver already on a trip, causing operational bottlenecks.
- **Compliance & Safety Violations:** Accidentally assigning drivers with suspended statuses or expired licenses.
- **Overloading Hazards:** Exceeding maximum vehicle load capacity, resulting in fines, wear and tear, and accidents.
- **Reactive Maintenance:** Missing mileage milestones and running vehicles to failure instead of performing preventive servicing.
- **Financial Blindspots:** Fragmented logging of fuel consumption, tolls, and maintenance bills, leading to hidden operating costs.

---

## 💡 Solution Overview

**TransitOps** solves these problems by providing a centralized, rules-enforced, and visually stunning digital cockpit.

Every transaction—whether registering a vehicle, hiring a driver, dispatching a trip, or logging fuel—is guarded by active validation scripts. Automated background jobs track license expiries and mileage thresholds, auto-generating maintenance tickets and removing non-compliant assets from the dispatch pool. Real-time cost roll-ups give financial analysts complete transparency over the total cost of ownership (TCO) and return on investment (ROI) for each vehicle.

---

## 📸 Visual Walkthrough

### 1. Live Guard Panel (Trip Form View)
The **Live Guard Panel** provides active status validation directly on the trip form:
* **Overloaded warning:** Shows when cargo weight exceeds the vehicle's capacity (Red alert).
* **Driver eligibility check:** Checks for expired licenses or suspended status.
* **Vehicle availability check:** Flags double-booking or in-shop statuses.

*(Tip: In a live demo, these elements update reactively before you hit save)*

### 2. OWL 19 Custom Analytics Dashboard
Real-time fleet performance graphs, utilization ratios, upcoming license expiry alerts, and action shortcuts.

### 3. Drag-and-Drop Kanban Board
Move vehicles and drivers dynamically between operational states.

---

## 🏗️ Architecture

TransitOps is built as a modular Odoo custom addon utilizing a model-view-controller relationship linked directly to Odoo's Web/OWL layer:

```mermaid
graph TD
    %% Core Models
    V[transit.vehicle] -->|One2Many| T[transit.trip]
    D[transit.driver] -->|One2Many| T
    V -->|One2Many| M[transit.maintenance]
    V -->|One2Many| FL[transit.fuel.log]
    V -->|One2Many| E[transit.expense]
    
    %% Wizards & Actions
    W1[transit.batch.dispatch.wizard] -->|Mutates| T
    W2[transit.complete.trip.wizard] -->|Updates| T
    
    %% Automatic Schedulers
    C1[Odometer Cron] -.->|Checks Mileage| V
    C1 -.->|Auto-Creates| M
    C2[License Expiry Cron] -.->|Alerts Safety Officers| D
```

### Data Relations & Computations
1. **Trip Lifecycle:** `Draft` ➔ `Dispatched` (locks vehicle & driver) ➔ `Completed` (triggers fuel log & odometer update) / `Cancelled` (releases vehicle & driver).
2. **Dynamic Operational Costs:**
   $$\text{Total Operational Cost} = \text{Fuel Logs Cost} + \text{Closed Maintenance Cost} + \text{Toll Costs}$$
3. **Vehicle ROI:**
   $$\text{ROI (\%)} = \left(\frac{\text{Total Trip Revenue} - \text{Total Operational Cost}}{\text{Acquisition Cost}}\right) \times 100$$

---

## 🛡️ Business Rules & Robustness Matrix

Our application enforces all core logistical and compliance constraints via multi-layered validation (PostgreSQL SQL constraints, Odoo API decorators, and UI indicators):

| Business Rule | Validation Level | Implementation Code File | Mechanics |
| :--- | :---: | :---: | :--- |
| **Unique Vehicle Registration** | Database (SQL) | [transit_vehicle.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_vehicle.py) | Enforces `Constraint` `UNIQUE(registration_number)` to prevent duplicate plates. |
| **No In-Shop/Retired Dispatch** | Python Logic | [transit_trip.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_trip.py) | `@api.constrains('vehicle_id')` blocks dispatching vehicles in `in_shop` or `retired` status. |
| **Driver License Expiry Checks** | Python Logic | [transit_trip.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_trip.py) | `@api.constrains('driver_id')` blocks assignments of drivers with expired licenses. |
| **No Double Booking** | Python State | [transit_trip.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_trip.py) | Blocks dispatching if a driver/vehicle is already marked `on_trip`. |
| **Cargo Capacity Safeguard** | Python & HTML | [transit_trip.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_trip.py) | `@api.constrains('cargo_weight')` blocks save if cargo weight > vehicle's capacity. |
| **License Expiry Alerting** | Cron Scheduler | [transit_cron_helpers.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_cron_helpers.py) | Automated daily scans check license expiry and alert safety officers if $\le 30$ days left. |
| **Odometer Milestone Maintenance** | Cron Scheduler | [transit_cron_helpers.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/models/transit_cron_helpers.py) | Automatic ticket creation + shifts vehicle status to `in_shop` when mileage threshold is met. |

---

## 💻 Technical Highlights & Odoo 19 Best Practices

1. **Class-Level Constraint Syntax:** Avoids Odoo 19 server warnings and crashes by utilizing the modern `models.Constraint` class instead of deprecated `_sql_constraints` lists.
2. **Chatter & Audit Log Integration:** Models inherit `mail.thread` and `mail.activity.mixin` to provide out-of-the-box system logging, collaborative notes, and automated activities for dispatchers.
3. **Optimized ORM Prefetching:** The OWL Dashboard controller utilizes `Promise.all` and Odoo's JS client-side `orm.searchRead()` API to load operational KPIs in a single batch, minimizing database queries.
4. **Transient Wizards:** Utilizes `TransientModel` for [batch_dispatch_wizard.py](file:///c:/Users/Admin/Downloads/odoo/custom_addons/transit_ops/wizard/batch_dispatch_wizard.py) to manage temporary user selections and state transitions without cluttering primary tables.

---

## 🚀 Core Features

### 1. Live Guard Panel (Pre-Flight Checks)
The form view of `transit.trip` features a **Live Guard Panel** (`dispatch_guard_html`) rendered via a custom HTML widget:
* **Reactive Validation:** Updates in real-time as users modify the cargo weight, vehicle, or driver.
* **Checks Performed:**
  * Checks if the assigned vehicle status is `available`.
  * Verifies if the driver's license status is `valid` or `expiring` (not `expired`).
  * Assesses cargo weight against the vehicle's `max_load_capacity`.
* **Visual Progress Bar:** An embedded capacity usage bar turns **Green** (safe), **Amber** (>90% full), or **Red** (overloaded, showing the exact overflow in kilograms).

### 2. Interactive Wizards & Operations
* **Batch Dispatch Wizard:** Select multiple draft trips in the list view and dispatch them in a single click. The wizard runs pre-flight safety and capacity checks for all selected records, generating a unified status report.
* **Complete Trip Wizard:** Prompts the operator for the `final_odometer` reading, `fuel_consumed` (liters), `fuel_cost`, and any `toll_cost`. It ensures the new odometer reading is greater than the previous one before closing the trip.

### 3. Automated Schedulers (Cron Jobs)
* **Odometer Milestone Checker:** Runs daily. If a vehicle accumulates 10,000+ km since its last maintenance date (or total since acquisition), the scheduler posts an alert to the vehicle's chatter and auto-creates an active maintenance record, shifting the vehicle to `In Shop` status.
* **License Expiry Alert:** Automatically scans driver records daily. If a driver's license expires in $\le 30$ days, it flags the status as `expiring`, sends warning alerts to the chatter, and logs scheduled activities for **Safety Officers** to process renewals.

### 4. Visual Analytics & Dynamic Dashboards
* **Kanban Boards:** Drag-and-drop cards for fleet vehicles and drivers, dynamically grouped by operational state.
* **Calendar Views:** Grid view displaying trip pipelines over weekly/monthly timelines.
* **OWL 19 Custom Dashboard:** A high-speed dashboard client action built using the Odoo Web Library (OWL). Displays real-time operational metrics like fleet utilization rate, active trips, and license warning tickers with one-click drilldowns.

---

## 🛠️ Tech Stack

* **Backend Engine:** Python 3.10+ & Odoo 19.0 Framework (using MVC decorators, API depends, constraints)
* **Database:** PostgreSQL (with indexed constraints)
* **Frontend Layer:** XML views, Odoo Web Client Action, custom Javascript (OWL Component), CSS variables, and modern glassmorphic theme overrides (`theme.css`)

---

## 📂 Module Structure

```text
transit_ops/
├── __init__.py
├── __manifest__.py                 # Addon metadata, asset registrations, & view load order
├── controllers/
│   └── main.py                     # HTTP endpoints for analytics & CSV exports
├── security/
│   ├── security.xml                # RBAC groups (Managers, Dispatchers, Safety, Finance)
│   └── ir.model.access.csv         # Comprehensive access control list (ACL) rules
├── data/
│   ├── sequence_data.xml           # Auto-generating Trip ID sequences
│   └── cron_data.xml               # Background daily schedulers
├── models/
│   ├── transit_vehicle.py          # Fleet registry, cost calculations, & SQL constraints
│   ├── transit_driver.py           # Driver profiles, license tracking, & eligibility
│   ├── transit_trip.py             # Pre-flight guard panel, lifecycle, & dispatch checks
│   ├── transit_maintenance.py      # Maintenance logs & auto-status management (In Shop)
│   ├── transit_fuel_log.py         # Fuel log registrations
│   ├── transit_expense.py          # Cost center aggregations
│   └── transit_cron_helpers.py     # Scheduler logic
├── wizard/
│   ├── batch_dispatch_wizard.py    # Multi-dispatch wizard logic
│   └── complete_trip_wizard.py     # Trip completion data capture
├── static/
│   ├── description/                # Module icon and descriptions
│   └── src/
│       ├── css/theme.css           # Custom CSS variables, glassmorphism, & dark mode compatibility
│       ├── js/dashboard.js         # OWL Dashboard Controller
│       └── xml/dashboard.xml        # OWL Dashboard Template
├── views/
│   ├── vehicle_views.xml           # Vehicle forms, lists, search, & kanbans
│   ├── driver_views.xml            # Driver forms, lists, search, & kanbans
│   ├── trip_views.xml              # Trip forms with the Live Guard Panel HTML widget
│   └── dashboard_client_action.xml # Custom action registration
└── tests/
    └── test_transit_ops.py         # Automated unit test suite
```

---

## 🔐 Security & RBAC

TransitOps enforces **Role-Based Access Control (RBAC)** across four explicit operations roles:

| Model | Fleet Manager | Dispatcher | Safety Officer | Financial Analyst |
| :--- | :---: | :---: | :---: | :---: |
| **transit.vehicle** | `CRUD` | `Read` | `Read` | `Read` |
| **transit.driver** | `CRUD` | `Read` | `CRUD` | `No Access` |
| **transit.trip** | `CRU` | `CRUD` | `Read` | `Read` |
| **transit.maintenance** | `CRUD` | `Read` | `No Access` | `No Access` |
| **transit.fuel.log** | `CRU` | `Read` | `No Access` | `CRUD` |
| **transit.expense** | `RU` | `No Access` | `No Access` | `CRUD` |

---

## 👥 Team & Roles

*   **Lead Backend Developer**: Implemented the Odoo custom models, state machine transitions, and cron schedulers.
*   **Frontend & OWL Developer**: Crafted the custom OWL 19 dashboard action, glassmorphic theme styles (`theme.css`), and the Live Guard Panel widget.
*   **QA & Release Engineer**: Authored the unit test suite, resolved Odoo 19 compatibility syntax, and established deployment configurations.

---

## ⚙️ Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL Server 14+
- Git

### 1. Clone & Set Up Directory
```powershell
git clone https://github.com/Gurjas2112/odoo_hackathon_2026.git
cd odoo_hackathon_2026
```

### 2. Configure Virtual Environment & Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements_filtered.txt
```

### 3. Start Odoo (Auto-Reload Enabled)
Configure the connection params in `odoo.conf` and spin up the service:
```powershell
.\venv\Scripts\python.exe odoo-src\odoo-bin -c odoo.conf -d hackathon_test_db -u transit_ops --dev=all
```
*The `--dev=all` flag enables automatic reloading of Python classes, controllers, and XML views upon file saves.*

### 4. Open in Web Browser
Open your browser and navigate to:
**`http://localhost:8069`**

---

## 🧪 Automated Verification (Test Suite)

TransitOps utilizes a comprehensive automated test suite (`TransactionCase`) covering all critical business limits:

*   **`test_01_vehicle_registration_uniqueness`**: Verifies that SQL-level uniqueness constraints prevent duplicate vehicle registrations.
*   **`test_02_retired_in_shop_vehicle_dispatch`**: Assures that vehicles marked `retired` or `in_shop` reject dispatch actions.
*   **`test_03_driver_eligibility_checks`**: Tests that expired-license or suspended-status drivers are rejected during dispatch validation.
*   **`test_04_double_booking_prevention`**: Ensures vehicles or drivers currently on a trip cannot be booked on concurrent trips.
*   **`test_05_cargo_capacity_overflow`**: Checks that cargo weight exceeding vehicle load limits raises validation errors.
*   **`test_06_dispatch_status_transitions`**: Asserts that trip dispatching dynamically transitions both vehicle and driver statuses to `on_trip`.
*   **`test_07_complete_status_transitions`**: Validates that completing a trip transitions assets back to `available`, records mileage, and updates operational costs.

Run the test suite using:
```powershell
.\venv\Scripts\python.exe odoo-src\odoo-bin -c odoo.conf -d hackathon_test_db --test-enable --stop-after-init -u transit_ops
```

*Expected output upon successful execution:*
```text
INFO hackathon_test_db odoo.tests.result: 0 failed, 0 error(s) of 10 tests when loading database 'hackathon_test_db'
```

---

## 📸 App Screenshots

Below are screenshots showcasing the TransitOps platform interface:

<div align="center">
  <h3>1. Dynamic Operations Dashboard</h3>
  <img src="Images/WhatsApp%20Image%202026-07-12%20at%204.52.10%20PM.jpeg" width="800" alt="Dynamic Operations Dashboard" />
  
  <h3>2. Trip Calendar Planner</h3>
  <img src="Images/WhatsApp%20Image%202026-07-12%20at%204.52.28%20PM.jpeg" width="800" alt="Trip Calendar Planner" />
  
  <h3>3. Trip Form & Pre-Flight Live Guard Panel</h3>
  <img src="Images/WhatsApp%20Image%202026-07-12%20at%204.52.51%20PM.jpeg" width="800" alt="Trip Form & Pre-Flight Live Guard Panel" />
  
  <h3>4. Interactive Driver Kanban Board</h3>
  <img src="Images/WhatsApp%20Image%202026-07-12%20at%204.53.00%20PM.jpeg" width="800" alt="Interactive Driver Kanban Board" />
  
  <h3>5. Interactive Vehicle Kanban Board</h3>
  <img src="Images/WhatsApp%20Image%202026-07-12%20at%204.53.19%20PM.jpeg" width="800" alt="Interactive Vehicle Kanban Board" />
</div>
