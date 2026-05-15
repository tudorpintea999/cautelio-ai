# Deployment — Cautelio AI

## Architecture

| What | Where | URL |
|------|-------|-----|
| Landing page + privacy policy | Vercel | cautelioai.xyz |
| Backend API | Contabo VPS | api.cautelioai.xyz |

---

## Part 1 — Landing page on Vercel

```bash
# From the website folder
cd projects/contract-compliance/website
vercel
```

Prompts:
- Project name: `cautelioai`
- Directory: `./`

In Vercel dashboard → Project → Settings → Domains → add `cautelioai.xyz` and `www.cautelioai.xyz`.

**Namecheap DNS for the landing page:**

| Type | Host | Value |
|------|------|-------|
| ALIAS | @ | `cname.vercel-dns.com` |
| CNAME | www | `cname.vercel-dns.com` |

Vercel provisions SSL automatically.

---

## Part 2 — Backend API on Contabo VPS

### Install dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx ufw
```

### Deploy

```bash
# From your local machine
scp -r projects/contract-compliance/backend user@YOUR_VPS_IP:/opt/cautelio/

# SSH in
ssh user@YOUR_VPS_IP

cd /opt/cautelio/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env  # add ANTHROPIC_API_KEY
```

### Systemd service

Create `/etc/systemd/system/cautelio.service`:

```ini
[Unit]
Description=Cautelio API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/cautelio/backend
EnvironmentFile=/opt/cautelio/backend/.env
ExecStart=/opt/cautelio/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /opt/cautelio
sudo systemctl daemon-reload
sudo systemctl enable cautelio
sudo systemctl start cautelio
sudo systemctl status cautelio
```

### Nginx

Create `/etc/nginx/sites-available/cautelio`:

```nginx
server {
    listen 80;
    server_name api.cautelioai.xyz;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 25M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/cautelio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL

```bash
sudo certbot --nginx -d api.cautelioai.xyz
sudo certbot renew --dry-run
```

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

**Namecheap DNS for the API:**

| Type | Host | Value |
|------|------|-------|
| A Record | api | YOUR_VPS_IP |

---

## Updating the backend

```bash
scp -r projects/contract-compliance/backend user@YOUR_VPS_IP:/opt/cautelio/
ssh user@YOUR_VPS_IP
cd /opt/cautelio/backend && source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart cautelio
```

---

## Verify everything

```bash
# API health check
curl https://api.cautelioai.xyz/docs

# Landing page
open https://cautelioai.xyz
```
