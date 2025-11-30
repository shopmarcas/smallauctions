# Docker Deployment Guide for Hetzner VPS

This guide explains how to deploy SmallAuctions using Docker and Docker Compose on your Hetzner VPS.

## 1. Install Docker on VPS
SSH into your server and run:
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker packages:
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 2. Prepare Project
Copy your project files to the server (e.g., using `scp` or `git clone`).
Create a `.env` file in the project root:
```bash
SECRET_KEY='your-prod-secret-key'
DEBUG=False
ALLOWED_HOSTS='your_server_ip,your_domain.com'
STRIPE_PUBLISHABLE_KEY='pk_live_...'
STRIPE_SECRET_KEY='sk_live_...'
POSTGRES_DB=smallauctions
POSTGRES_USER=smallauctionsuser
POSTGRES_PASSWORD=password
POSTGRES_HOST=db
```

## 3. Run with Docker Compose
```bash
sudo docker compose up -d --build
```
This will start the Django app and a PostgreSQL database in the background.

## 4. Database Migrations
Run migrations inside the container:
```bash
sudo docker compose exec web python manage.py migrate
sudo docker compose exec web python manage.py createsuperuser
```

## 5. Accessing the App
Your app should now be running on `http://your_server_ip:8000`.

**Note**: For production, you should put Nginx in front of Docker, or use a reverse proxy like Traefik, to handle SSL (HTTPS) and port 80.
