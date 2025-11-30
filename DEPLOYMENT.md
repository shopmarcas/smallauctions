# Deployment Plan for SmallAuctions

## 1. VPS Setup (Hetzner CX33)
- You are using a Hetzner CX33 VPS.
- Ensure it is installed with **Ubuntu 22.04** (or later).
- SSH into the server: `ssh root@your_server_ip`

## 2. System Dependencies
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql libpq-dev
```

## 3. Project Setup
- Clone the repository or copy files to `/var/www/smallauctions`.
- Create virtual environment:
```bash
cd /var/www/smallauctions
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

## 4. Environment Variables
Create a `.env` file or set env vars in systemd service:
```bash
export SECRET_KEY='your-prod-secret-key'
export DEBUG=False
export ALLOWED_HOSTS='your_domain.com,your_droplet_ip'
export STRIPE_PUBLISHABLE_KEY='pk_live_...'
export STRIPE_SECRET_KEY='sk_live_...'
```

## 5. Database (PostgreSQL)
```bash
sudo -u postgres psql
CREATE DATABASE smallauctions;
CREATE USER smallauctionsuser WITH PASSWORD 'password';
ALTER ROLE smallauctionsuser SET client_encoding TO 'utf8';
ALTER ROLE smallauctionsuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE smallauctionsuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE smallauctions TO smallauctionsuser;
\q
```
Update `settings.py` to use PostgreSQL if desired (requires `dj-database-url` or manual config). For MVP, SQLite is fine but ensure permissions on `db.sqlite3` allow write by the web user.

## 6. Gunicorn Setup
Create `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/smallauctions
ExecStart=/var/www/smallauctions/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/smallauctions/smallauctions.sock smallauctions.wsgi:application

[Install]
WantedBy=multi-user.target
```
Start and enable:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 7. Nginx Setup
Create `/etc/nginx/sites-available/smallauctions`:
```nginx
server {
    listen 80;
    server_name your_domain.com your_droplet_ip;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /var/www/smallauctions;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/smallauctions/smallauctions.sock;
    }
}
```
Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/smallauctions /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Final Steps
- Run migrations: `python manage.py migrate`
- Collect static files: `python manage.py collectstatic`
- Create superuser: `python manage.py createsuperuser`
