# Manual Feature Store Prerequisites Setup Commands

## Quick Setup Commands (Copy and paste these one by one)

```cmd
# 1. Check if we're in the right directory
dir docker-compose.yml

# 2. Check Docker is running
docker --version
docker-compose --version

# 3. Create .env file if needed
if not exist .env copy .env.template .env

# 4. Create required directories
mkdir data 2>nul
mkdir data\feature_store 2>nul
mkdir data\test 2>nul
mkdir logs 2>nul
mkdir reports 2>nul

# 5. Build Docker image
docker-compose build dev

# 6. Start services one by one
docker-compose up -d postgres
timeout /t 10 /nobreak >nul
docker-compose up -d redis
timeout /t 5 /nobreak >nul
docker-compose up -d dev
timeout /t 10 /nobreak >nul

# 7. Check service status
docker-compose ps

# 8. Test basic connections
docker-compose exec -T postgres pg_isready -U mlops_user -d mlops
docker-compose exec -T redis redis-cli ping
docker-compose exec -T dev python --version
```

## If you get encoding errors, use PowerShell instead:

```powershell
# Run this in PowerShell (not CMD)
.\setup-feature-store-prerequisites.ps1
```

## Or use the corrected batch file:

```cmd
# Use the English-only version
.\setup-feature-store-prerequisites.bat
```

## Manual validation (if scripts fail):

```cmd
# Enter the container and test manually
docker-compose exec dev bash

# Inside container, run:
python -c "
import redis, psycopg2
print('Testing Redis...')
r = redis.Redis(host='redis', port=6379)
print('Redis ping:', r.ping())

print('Testing PostgreSQL...')
conn = psycopg2.connect(host='postgres', database='mlops', user='mlops_user', password='mlops_password')
print('PostgreSQL connected successfully')
conn.close()

print('All basic tests passed!')
"
```
