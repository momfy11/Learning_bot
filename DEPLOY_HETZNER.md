# Deploy Learning Bot to Hetzner Cloud VPS

Step-by-step guide to deploy your Learning Bot using Docker.

## Server Information

- **Server**: coolify-ubuntu-8gb-nbg1-1
- **IP**: 46.225.81.127
- **Region**: Nuremberg (Germany)
- **RAM**: 8GB
- **OS**: Ubuntu 22.04

---

## Step 1: Set Up SSH Key (Recommended)

Using SSH keys is more secure than passwords and removes the need to enter password each time.

### On Your Local Machine (Windows)

**Generate SSH key:**

```bash
# Open Git Bash or PowerShell
ssh-keygen -t ed25519 -f ~/.ssh/hetzner_key -C "learning-bot"

# Press Enter for all prompts (no passphrase needed for now)
# This creates:
# - ~/.ssh/hetzner_key (private key - KEEP SECRET!)
# - ~/.ssh/hetzner_key.pub (public key - add to server)

# View your public key
type ~/.ssh/hetzner_key.pub
```

Save the output (the long string starting with `ssh-ed25519...`)

---

## Step 2: First Login & Add SSH Key

### Login with password (one time)

```bash
# Connect to server
ssh root@46.225.81.127

# Enter password: mhRarTMfrUCtNLbXLtp
```

You'll be prompted to change your password on first login.

### Add your public key to server

Once logged in, run these commands on the server:

```bash
# Create SSH directory
mkdir -p ~/.ssh

# Edit authorized_keys file
nano ~/.ssh/authorized_keys
```

Paste your public key (from `~/.ssh/hetzner_key.pub` on your local machine), save with **Ctrl+X**, **Y**, **Enter**

```bash
# Set correct permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Exit SSH
exit
```

### Test SSH key login

Back on your local machine:

```bash
# Login with key (no password needed!)
ssh -i ~/.ssh/hetzner_key root@46.225.81.127
```

If this works, you can now use SSH keys instead of passwords!

---

## Step 3: Update System & Install Docker

On the server:

```bash
# Update system packages
apt update && apt upgrade -y

# Install Docker and Git
apt install -y docker.io docker-compose-plugin git

# Verify installation
docker --version
docker compose version

# Enable Docker to run on startup
systemctl enable docker
systemctl start docker
```

---

## Step 4: Clone Your Repository

## Step 4: Clone Your Repository

On the server:

```bash
cd /root
git clone https://github.com/momfy11/Learning_bot.git
cd Learning_bot

# See what files are there
ls -la
```

This downloads your entire project (backend, frontend, docker configs).

---

## Step 5: Create .env File for Docker

The docker-compose needs environment variables for:
- Database password
- Mistral API key
- Server URLs

```bash
# Copy the example template
cp .env.docker.example .env

# Edit it
nano .env
```

Update these values:

```
POSTGRES_DB=learning_bot
POSTGRES_USER=learning_bot_user
POSTGRES_PASSWORD=SET_A_SECURE_PASSWORD_HERE

SECRET_KEY=GENERATE_RANDOM_STRING
MISTRAL_API_KEY=YOUR_MISTRAL_KEY
MISTRAL_MODEL=mistral-small-2506
EMBEDDING_MODEL=all-MiniLM-L6-v2
FRONTEND_URL=http://46.225.81.127
VITE_API_URL=http://46.225.81.127:8000
MAX_CONTEXT_TOKENS=2000
TOP_K_RESULTS=3
```

**To generate a random SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the file: **Ctrl+X**, **Y**, **Enter**

---

## Step 6: Review Docker Configuration

Let's check what we're about to start:

```bash
# View the docker-compose.yml to understand the structure
cat docker-compose.yml
```

This file defines 3 services:
1. **db** - PostgreSQL database
2. **backend** - FastAPI server
3. **frontend** - Nginx web server

Each service has:
- Image/Dockerfile
- Environment variables
- Volume mounts (persistent storage)
- Port mappings

---

## Step 7: Build Docker Images

This reads the Dockerfiles and creates container images:

```bash
docker compose build
```

What happens:
- Backend Dockerfile: Installs Python 3.11 + requirements.txt dependencies
- Frontend Dockerfile: Builds React with Vite, serves with Nginx
- Database: Uses official PostgreSQL image

**First build takes 5-10 minutes** (downloading and compiling dependencies).

---

## Step 8: Start All Services

```bash
# Start in background (-d = detached)
docker compose up -d

# Watch for any startup issues
docker compose logs -f
```

Press **Ctrl+C** to exit logs view.

This starts:
- **PostgreSQL** - listening on port 5432 (internal to Docker)
- **FastAPI** - listening on port 8000
- **Nginx** - listening on port 80 (your frontend)

---

## Step 9: Verify Services are Running

```bash
# Check status of all containers
docker compose ps
```

Expected output:
```
NAME                  STATUS
learning_bot-db-1        Up (healthy)
learning_bot-backend-1   Up
learning_bot-frontend-1  Up
```

All should say "Up".

---

## Step 10: Check Backend is Ready

```bash
# View backend startup logs
docker compose logs backend
```

Look for:
```
🚀 Starting Learning Bot...
✅ Database tables created
📂 Scanning documents folder...
✅ Learning Bot ready!
```

If you see errors, we can debug. Common issues:
- Database not ready yet (wait 10 seconds, restart backend)
- Missing Mistral API key (check .env file)

---

## Step 11: Test from Your Local Computer

Open your browser:

**Frontend (Chat UI):**
```
http://46.225.81.127
```
You should see the login page.

**Backend API Docs:**
```
http://46.225.81.127:8000/api/docs
```
You should see Swagger UI with all API endpoints.

**Health Check:**
```
curl http://46.225.81.127:8000/health
```
Should return:
```json
{"status": "healthy", "service": "learning-bot-api"}
```

---

## Step 12: Test the Full Flow

### Create an Account
1. Go to http://46.225.81.127
2. Click "Register"
3. Create an account

### Upload a Document
1. Log in
2. Click "Documents" tab
3. Click "Upload Document"
4. Select a PDF or text file

**First upload takes longer** (embedding model downloads ~500MB on first use)

### Test RAG Search
1. Go to "Chat" tab
2. Ask a question about your document
3. The bot should search and cite the document

---

## Useful Docker Commands

```bash
# View logs from specific service
docker compose logs backend
docker compose logs frontend
docker compose logs db

# Follow logs in real-time
docker compose logs -f

# Restart a service
docker compose restart backend

# Stop all services
docker compose stop

# Start again
docker compose start

# Full restart
docker compose down && docker compose up -d

# Update code and rebuild
cd ~/Learning_bot
git pull origin main
docker compose up -d --build
```

---

## Database Connection (Optional)

If you want to access PostgreSQL from your local machine (e.g., with DataGrip):

1. Edit `docker-compose.yml` and uncomment the ports for `db` service:
```yaml
db:
  ports:
    - "5432:5432"
```

2. Restart:
```bash
docker compose down && docker compose up -d
```

3. Connect from DataGrip:
- Host: `46.225.81.127`
- Port: `5432`
- Database: `learning_bot`
- User: `learning_bot_user`
- Password: (from .env file)

---

## Monitoring & Maintenance

```bash
# Check server disk usage
df -h

# Check container resource usage
docker stats

# View system logs
journalctl -xe

# Restart all services
docker compose restart
```

---

## Next Steps

1. ✅ Deploy application
2. ✅ Test uploading documents
3. ✅ Test chat with RAG
4. Later: Set up HTTPS with Let's Encrypt
5. Later: Add firewall rules
6. Later: Set up automated backups

**View only backend logs (live):**
```bash
docker compose logs -f backend
```

**Stop services:**
```bash
docker compose down
```

**Restart services:**
```bash
docker compose restart
```

**Check disk usage:**
```bash
docker system df
```

**Access PostgreSQL from server:**
```bash
docker exec -it learning_bot-db-1 psql -U learning_bot_user -d learning_bot
```

---

## Troubleshooting

**Backend won't start?**
```bash
docker compose logs backend
```
Look for error messages.

**Port 80 already in use?**
```bash
sudo lsof -i :80
```

**Container keeps restarting?**
Check logs: `docker compose logs <service-name>`

**Want to deploy new code changes?**
```bash
git pull
docker compose build
docker compose up -d
```

---

## Next: Domain & HTTPS

Once everything works, we can:
1. Point your domain to 46.225.81.127
2. Set up Caddy reverse proxy for HTTPS

Ask when ready!
