# Offline / LAN Server Setup

## Requirements
- One Windows/Linux PC as local server
- All POS terminals on same WiFi/LAN network

## Setup Steps

1. Install PostgreSQL on local server PC
2. Install Redis on local server PC
3. Clone the project on local server PC
4. Set .env with LAN server IP:

   DB_HOST=192.168.1.100     ← local server IP
   ALLOWED_HOSTS=192.168.1.100,localhost

5. Run Django on LAN:
   python manage.py runserver 0.0.0.0:8000

6. All POS terminals connect to:
   http://192.168.1.100:8000/api/

## When Internet Restores
- System continues working normally
- Cloud sync can be added as future enhancement