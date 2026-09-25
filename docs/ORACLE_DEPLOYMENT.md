# Oracle Cloud Always Free ARM64 Native Deployment Guide (No Docker)

This guide describes how to natively deploy the Airfare Index project directly on an Oracle Cloud Infrastructure (OCI) Always Free VM (Ubuntu 22.04/24.04 ARM64) using Nginx, Systemd, and Python.

## 1. SSH into Your Oracle Server
Connect to your cloud server using your SSH key:
```bash
ssh -i /path/to/your/private_key.pem ubuntu@YOUR_ORACLE_PUBLIC_IP
```

## 2. Update System & Open Firewalls
Oracle blocks port 80 by default in iptables. Open it up:
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

## 3. Install Required Software
Install Python, Nginx, and Node.js:
```bash
# Install Python and Nginx
sudo apt-get install -y python3-pip python3-venv nginx libpq-dev python3-dev gcc

# Install Node.js (for building React)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 4. Clone the Code
```bash
cd ~
git clone https://github.com/Srajan05-ui/airfareindex-.git
cd airfareindex-
```

## 5. Set Up the Python Backend
Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_deploy.txt
```

Create your `.env` file with the Neon database URL:
```bash
nano .env
```
Add:
```env
DATABASE_URL=postgresql://YOUR_NEON_USERNAME:YOUR_NEON_PASSWORD@ep-YOUR-NEON-ID.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
CORS_ORIGINS=*
```

## 6. Run FastAPI as a Background Service
We use `systemd` so the backend stays alive even if you close the terminal.
```bash
sudo nano /etc/systemd/system/airfare-backend.service
```
Paste the following (assuming your username is `ubuntu`):
```ini
[Unit]
Description=Airfare Index FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/airfareindex-
EnvironmentFile=/home/ubuntu/airfareindex-/.env
ExecStart=/home/ubuntu/airfareindex-/venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
Start and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start airfare-backend
sudo systemctl enable airfare-backend
```

## 7. Build the React Frontend
```bash
cd ~/airfareindex-/frontend
npm install
npm run build
```

## 8. Configure Nginx
Route web traffic to the React app, and `/api` to FastAPI.
```bash
sudo nano /etc/nginx/sites-available/airfare
```
Paste this configuration:
```nginx
server {
    listen 80;
    server_name _;
    
    # Point to the React build folder
    root /home/ubuntu/airfareindex-/frontend/dist;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/javascript application/json;

    # Proxy /api requests to FastAPI
    location /api/ {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve React SPA
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/airfare /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 9. You're Done!
Go to your browser and enter your **Oracle VM Public IP Address**.
You should see the React dashboard loading data smoothly from Neon!

**To check backend logs if something fails:**
```bash
sudo journalctl -u airfare-backend -f
```
