# devProductivity Database Setup Guide

## Overview
This project is configured to use a Dockerized PostgreSQL database, based on the provided best practices.

## Prerequisites
1. Install Docker Desktop for Windows
2. Ensure Docker service is running

## Setup Steps

### 1. Create Environment Variables File
Create a `.env` file in the project root directory:

```bash
# GitHub Token
GITHUB_TOKEN="your_github_token_here"

# PostgreSQL Database Configuration
POSTGRES_DB=devProductivity
POSTGRES_USER=devProductivity
POSTGRES_PASSWORD=your_strong_password_here

# Django Database Configuration
DATABASE_URL=postgresql://devProductivity:your_strong_password_here@localhost:5432/devProductivity
```

**Important**: Replace `your_strong_password_here` with a strong password!

### 2. Start PostgreSQL Container
```bash
docker compose up -d db
```

### 3. Verify Container Status
```bash
docker ps
```

You should see a container named `devProductivity_pg` running.

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Start Django Development Server
```bash
python manage.py runserver
```

## Configuration Details

### Docker Compose Configuration
- **Image**: `postgres:16-alpine`
- **Container Name**: `devProductivity_pg`
- **Port Mapping**: `5432:5432`
- **Data Persistence**: Local directory `./data/postgres`
- **Network**: Custom bridge network `backend`

### Django Database Configuration
- **Engine**: `django.db.backends.postgresql`
- **Host**: `127.0.0.1` (Docker container exposed to host)
- **Port**: `5432`
- **Database Name**: Read from environment variable `POSTGRES_DB`
- **Username**: Read from environment variable `POSTGRES_USER`
- **Password**: Read from environment variable `POSTGRES_PASSWORD`

## Common Commands

### Container Management
```bash
# Start database
docker compose up -d db

# Stop database
docker compose down

# View container logs
docker logs devProductivity_pg

# Enter container
docker exec -it devProductivity_pg psql -U devProductivity -d devProductivity
```

### Database Operations
```bash
# Connect to database
psql -h localhost -U devProductivity -d devProductivity

# Backup database
docker exec devProductivity_pg pg_dump -U devProductivity devProductivity > backup.sql

# Restore database
docker exec -i devProductivity_pg psql -U devProductivity -d devProductivity < backup.sql
```

## Feature Advantages

### ✅ Zero Conflicts
- Multiple projects each use independent PostgreSQL containers
- Different versions of PostgreSQL can coexist

### ✅ Fast Version Switching
- Modify image tag in `docker-compose.yml` to switch versions
- Example: `postgres:15-alpine` → `postgres:16-alpine`

### ✅ Easy Migration
- Data stored in local project directory, easy to migrate to other machines
- Entire environment configuration in code, convenient for version control

### ✅ Quick Cleanup
- Delete container and data directory to completely clean database environment
- No system pollution concerns

## Troubleshooting

### Container Cannot Start
1. Check if port 5432 is occupied
2. Confirm Docker Desktop is running
3. Check configuration in `.env` file

### Django Cannot Connect to Database
1. Confirm container is running: `docker ps`
2. Check database configuration in `.env` file
3. Confirm firewall is not blocking port 5432

### Data Loss
- Data is stored in local directory `./data/postgres`
- As long as the directory is not deleted, data will persist
- Recommend regular backups of important data

## Security Recommendations

1. **Strong Password**: Use complex database passwords
2. **Environment Variables**: Do not commit passwords to version control
3. **Network Isolation**: Consider using internal networks in production
4. **Regular Backups**: Set up automated backup strategies
5. **Permission Control**: Use different database users for different environments

## Production Environment Considerations

1. **Performance Tuning**: Adjust PostgreSQL configuration based on actual load
2. **Monitoring**: Set up database performance monitoring
3. **Backup Strategy**: Implement automated backup and recovery testing
4. **High Availability**: Consider master-slave replication or cluster deployment
5. **Security Hardening**: Use SSL connections, restrict network access

---

*Docker-based PostgreSQL solution providing stable, scalable database services for the devProductivity project.* 