# Oracle Cloud Always Free ARM64 Deployment Guide

This guide describes how to deploy the Airfare Index project on an Oracle Cloud Infrastructure (OCI) Always Free VM (VM.Standard.A1.Flex, ARM64) using Docker Compose.

## 1. Oracle VM Requirements

- **Instance Type:** VM.Standard.A1.Flex (ARM64)
- **OS Image:** Canonical Ubuntu 22.04 / 24.04
- **OCPU:** 1 - 4
- **RAM:** 6GB - 24GB
- **Boot Volume:** 50GB minimum
- **Public IP:** Assigned during creation

## 2. Oracle VCN Ingress Requirements

Ensure your Oracle Virtual Cloud Network (VCN) allows incoming HTTP and HTTPS traffic:
1. Open the Oracle Cloud Console.
2. Navigate to **Networking** -> **Virtual Cloud Networks**.
3. Select your VCN, then click **Security List**.
4. Add Ingress Rules:
   - **Source CIDR:** `0.0.0.0/0`
   - **Protocol:** TCP
   - **Destination Port:** `80` (HTTP)
   - **Destination Port:** `443` (HTTPS - optional but recommended for later)

## 3. SSH Setup & Firewall Requirements

SSH into the newly created VM:
```bash
ssh -i /path/to/your/private_key.pem ubuntu@YOUR_PUBLIC_IP
```

**Open the firewall on the VM:**
Oracle's default Ubuntu images have strict iptables rules. Open port 80:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

## 4. Docker Installation

Install Docker and Docker Compose on Ubuntu ARM64:
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow non-root Docker usage (requires re-login to take effect)
sudo usermod -aG docker $USER
```
*Note: Log out and log back in, or run `newgrp docker`.*

## 5. Git Clone

Clone the repository:
```bash
git clone https://github.com/Srajan05-ui/airfareindex-.git
cd airfareindex-
```

## 6. `.env` Setup

Create the `.env` file on the server. **Do not commit this file to GitHub.**
```bash
nano .env
```
Add the Neon PostgreSQL Database URL:
```env
DATABASE_URL=postgresql://YOUR_NEON_USERNAME:YOUR_NEON_PASSWORD@ep-YOUR-NEON-ID.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
CORS_ORIGINS=*
```

## 7. Docker Compose Commands

Build and start the application in detached mode:
```bash
docker compose build
docker compose up -d
```

## 8. Verifying Connectivity

Once the containers are up, test local connectivity on the VM:
```bash
# Test Nginx routing to React SPA
curl http://localhost/

# Test Nginx proxying to FastAPI backend health check
curl http://localhost/api/health

# Test Nginx proxying to FastAPI data endpoints
curl http://localhost/api/index/latest
```

## 9. Troubleshooting & Logs

To view logs for both frontend and backend:
```bash
docker compose logs -f
```

To view logs for only the backend (useful for API errors):
```bash
docker compose logs -f backend
```

## 10. Restarting and Updating

To restart services:
```bash
docker compose restart
```

To update the deployment with new code from GitHub:
```bash
git pull origin master
docker compose build
docker compose up -d
```
