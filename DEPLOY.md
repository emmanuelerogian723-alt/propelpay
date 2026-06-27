# PropelPay Deployment Guide

## Oracle Cloud Always Free (Recommended — Truly Free Forever)

### Step 1: Launch VM
- Go to cloud.oracle.com
- Compute → Instances → Create Instance
- Shape: VM.Standard.A1.Flex (4 CPU, 24GB RAM) — ALWAYS FREE
- OS: Ubuntu 22.04
- Enable public IP

### Step 2: Install Docker
```bash
ssh ubuntu@YOUR_IP
sudo apt update && sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu
newgrp docker
```

### Step 3: Clone & Configure
```bash
git clone https://github.com/YOUR_REPO/propelpay
cd propelpay
cp .env.example .env
nano .env  # Fill in your keys
```

### Step 4: Deploy
```bash
docker-compose up -d
```

Your app is now live at http://YOUR_IP:8000

### Step 5: Domain + HTTPS (Free)
- Point your domain to YOUR_IP
- Install Nginx + Certbot:
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

## Free Database Options
- SQLite: Default, built in, works great for <10,000 users
- Neon.tech: Free PostgreSQL (0.5GB) — best for production
- Supabase: Free PostgreSQL (500MB)

## Free Email Options
- Gmail SMTP: 500 emails/day free (use App Password)
- Brevo (Sendinblue): 300 emails/day free
- Resend.com: 3,000 emails/month free

## Free Monitoring
- UptimeRobot: Free uptime monitoring + email alerts
- Sentry.io: Free error tracking (5,000 errors/month)
