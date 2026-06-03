# SmartSlot — Universal Office Resource Booking System

A dual-platform, multi-tenant office resource booking system built for organisations in Malawi.

**Final Year ICT Project — COM 422 | University of Malawi | June 2026**

**Team:** Lusekero Mwanjoka, Chimwemwe Katenje, Sifiso Chitowe, Chipulumutso Phiri  
**Supervisor:** Mr. Chikondi Sepula

---

## What is SmartSlot?

SmartSlot replaces manual resource booking methods (WhatsApp, Excel, notebooks) with a centralised digital platform that includes real-time availability, mobile money payments, and QR code verification.

## Live System

- **Web Dashboard:** https://smartslot-bh9c.onrender.com/
- **Mobile App:** Android APK (Flutter)

## Project Structure
```
Smart-Slot-Project/
├── smartslot/                  ← Django Web Backend
│   ├── apps/
│   ├── config/
│   ├── templates/
│   └── manage.py
└── smartslot_android_app/      ← Flutter Mobile App
    ├── lib/
    └── pubspec.yaml
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1.5 (Python) |
| Mobile App | Flutter (Dart) |
| Database | Supabase (PostgreSQL) |
| Authentication | Supabase Auth (JWT) |
| Payments | PayChangu |
| Hosting | Render |

## Running Locally

### Django Backend
cd smartslot
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py runserver

### Flutter Mobile App
cd smartslot_android_app
flutter pub get
flutter run

## Environment Variables

Create a `.env` file in the `smartslot/` directory with:
DATABASE_URL=your_supabase_connection_string
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
PAYCHANGU_SECRET_KEY=your_paychangu_secret_key

## User Roles

| Role | Platform | Capabilities |
|------|----------|-------------|
| Super Admin | Web | Manages all organisations |
| Organisation Admin | Web | Manages resources and members for their organisation |
| Employee | Mobile App | Browses and books resources |
| External User | Mobile App | Books publicly available resources |
