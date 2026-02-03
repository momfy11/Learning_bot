# PostgreSQL Setup Guide

This project uses **PostgreSQL** for production database. Here's how to set it up.

## Local Development

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Run installer, remember the password you set for `postgres` user
- PostgreSQL runs on `localhost:5432` by default

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

### 2. Create Database

```bash
# Login as postgres user
psql -U postgres

# In psql shell:
CREATE DATABASE learning_bot;
CREATE USER learning_bot WITH PASSWORD 'your_secure_password';
ALTER ROLE learning_bot SET client_encoding TO 'utf8';
ALTER ROLE learning_bot SET default_transaction_isolation TO 'read committed';
ALTER ROLE learning_bot SET default_transaction_deferrable TO on;
ALTER ROLE learning_bot SET default_transaction_read_committed TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE learning_bot TO learning_bot;
\q  # Exit psql
```

### 3. Update .env

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your PostgreSQL credentials
DATABASE_URL=postgresql+asyncpg://learning_bot:your_secure_password@localhost:5432/learning_bot
```

### 4. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Initialize Database

```bash
# The tables will be created automatically on first run via SQLAlchemy
# Just start the server and it will create tables
cd backend
uvicorn app.main:app --reload
```

## Useful PostgreSQL Commands

```bash
# Connect to database
psql -U learning_bot -d learning_bot

# List databases
\l

# List tables in current database
\dt

# Check database size
SELECT pg_size_pretty(pg_database_size('learning_bot'));

# Backup database
pg_dump -U learning_bot learning_bot > backup.sql

# Restore from backup
psql -U learning_bot learning_bot < backup.sql
```

---

## Migrate from SQLite (if needed)

If you have existing SQLite data:

```bash
# Export SQLite data (manual approach)
# 1. Keep your old SQLite database
# 2. Run the server with PostgreSQL - it will create empty tables
# 3. Manually migrate important data or recreate accounts

# Easier approach: Start fresh with PostgreSQL
# 1. Delete learning_bot.db
# 2. Set up PostgreSQL as above
# 3. Create new accounts/documents
```

---

## Troubleshooting

**"Connection refused"**
- Make sure PostgreSQL service is running
- Check DATABASE_URL is correct
- Verify port 5432 is accessible

**"FATAL: password authentication failed"**
- Check username and password in DATABASE_URL
- Reset password: `ALTER USER learning_bot WITH PASSWORD 'newpassword';`

**"Database does not exist"**
- Create it: `CREATE DATABASE learning_bot;`
- Make sure user has privileges

**AsyncPG errors**
- Install: `pip install asyncpg`
- Update requirements.txt has `asyncpg==0.29.0`
