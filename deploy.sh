#!/bin/bash

# Charity Nepal Backend Deployment Script
# This script handles the deployment of the charity management system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_NAME="charity_nepal"
PYTHON_VERSION="3.11"
VENV_NAME="venv"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install UV if not present
install_uv() {
    if ! command_exists uv; then
        log_info "Installing UV package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
        log_success "UV installed successfully"
    else
        log_info "UV is already installed"
    fi
}

# Function to setup project environment
setup_environment() {
    log_info "Setting up project environment..."
    
    # Initialize UV project if needed
    if [ ! -f "pyproject.toml" ]; then
        log_info "Initializing UV project..."
        uv init
    fi
    
    # Install dependencies
    log_info "Installing dependencies with UV..."
    uv sync
    
    log_success "Environment setup completed"
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Make migrations
    uv run python manage.py makemigrations
    
    # Apply migrations
    uv run python manage.py migrate
    
    log_success "Database migrations completed"
}

# Function to collect static files
collect_static() {
    log_info "Collecting static files..."
    uv run python manage.py collectstatic --noinput
    log_success "Static files collected"
}

# Function to create superuser
create_superuser() {
    log_info "Creating superuser account..."
    
    echo "Please enter superuser details:"
    read -p "Email: " ADMIN_EMAIL
    read -s -p "Password: " ADMIN_PASSWORD
    echo
    
    uv run python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='$ADMIN_EMAIL').exists():
    User.objects.create_superuser(
        email='$ADMIN_EMAIL',
        password='$ADMIN_PASSWORD',
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF
    
    log_success "Superuser setup completed"
}

# Function to run tests
run_tests() {
    log_info "Running test suite..."
    
    # Run Django tests
    uv run python manage.py test --verbosity=2
    
    # Run custom test script
    if [ -f "run_tests.py" ]; then
        uv run python run_tests.py
    fi
    
    log_success "Tests completed"
}

# Function to start development server
start_dev_server() {
    log_info "Starting development server..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start server
    uv run python manage.py runserver 127.0.0.1:8000
}

# Function to start production server with Gunicorn
start_prod_server() {
    log_info "Starting production server with Gunicorn..."
    
    # Install gunicorn if not present
    uv add gunicorn
    
    # Create logs directory
    mkdir -p logs
    
    # Start Gunicorn
    uv run gunicorn charity_backend.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --worker-class gevent \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 30 \
        --keep-alive 2 \
        --log-level info \
        --log-file logs/gunicorn.log \
        --access-logfile logs/gunicorn_access.log \
        --error-logfile logs/gunicorn_error.log \
        --capture-output \
        --daemon
    
    log_success "Production server started"
}

# Function to setup Celery
setup_celery() {
    log_info "Setting up Celery workers..."
    
    # Start Celery worker in background
    uv run celery -A charity_backend worker --loglevel=info --detach \
        --pidfile=logs/celery_worker.pid \
        --logfile=logs/celery_worker.log
    
    # Start Celery beat scheduler
    uv run celery -A charity_backend beat --loglevel=info --detach \
        --pidfile=logs/celery_beat.pid \
        --logfile=logs/celery_beat.log \
        --schedule=logs/celerybeat-schedule
    
    log_success "Celery workers started"
}

# Function to setup with Docker
setup_docker() {
    log_info "Setting up with Docker..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Build and start containers
    docker-compose up --build -d
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 10
    
    # Run migrations in container
    docker-compose exec web python manage.py migrate
    
    log_success "Docker setup completed"
}

# Function to run API tests
test_api() {
    log_info "Running API integration tests..."
    
    if [ -f "test_api.py" ]; then
        uv run python test_api.py --wait 10
    else
        log_warning "API test script not found"
    fi
}

# Function to generate SSL certificate
generate_ssl() {
    log_info "Generating SSL certificate for HTTPS..."
    
    mkdir -p ssl
    
    # Generate self-signed certificate for development
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 \
        -subj "/C=NP/ST=Bagmati/L=Kathmandu/O=CharityNepal/CN=localhost" \
        -keyout ssl/server.key \
        -out ssl/server.crt
    
    log_success "SSL certificate generated"
}

# Function to backup database
backup_database() {
    log_info "Creating database backup..."
    
    mkdir -p backups
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # Backup SQLite database
    if [ -f "db.sqlite3" ]; then
        cp db.sqlite3 "backups/db_backup_$TIMESTAMP.sqlite3"
        log_success "Database backup created: backups/db_backup_$TIMESTAMP.sqlite3"
    else
        log_warning "Database file not found"
    fi
}

# Function to show system status
show_status() {
    log_info "System Status:"
    echo "===================="
    
    # Check if server is running
    if pgrep -f "manage.py runserver" > /dev/null; then
        log_success "Django development server is running"
    elif pgrep -f "gunicorn" > /dev/null; then
        log_success "Gunicorn production server is running"
    else
        log_warning "No Django server detected"
    fi
    
    # Check Celery workers
    if [ -f "logs/celery_worker.pid" ] && kill -0 $(cat logs/celery_worker.pid) 2>/dev/null; then
        log_success "Celery worker is running"
    else
        log_warning "Celery worker is not running"
    fi
    
    # Check Celery beat
    if [ -f "logs/celery_beat.pid" ] && kill -0 $(cat logs/celery_beat.pid) 2>/dev/null; then
        log_success "Celery beat is running"
    else
        log_warning "Celery beat is not running"
    fi
    
    # Check Docker containers
    if command_exists docker-compose; then
        if docker-compose ps | grep -q "Up"; then
            log_success "Docker containers are running"
        else
            log_warning "Docker containers are not running"
        fi
    fi
}

# Function to stop all services
stop_services() {
    log_info "Stopping all services..."
    
    # Stop Django server
    pkill -f "manage.py runserver" || true
    pkill -f "gunicorn" || true
    
    # Stop Celery
    if [ -f "logs/celery_worker.pid" ]; then
        kill $(cat logs/celery_worker.pid) || true
        rm -f logs/celery_worker.pid
    fi
    
    if [ -f "logs/celery_beat.pid" ]; then
        kill $(cat logs/celery_beat.pid) || true
        rm -f logs/celery_beat.pid
    fi
    
    # Stop Docker containers
    if command_exists docker-compose; then
        docker-compose down
    fi
    
    log_success "All services stopped"
}

# Main deployment function
deploy() {
    log_info "Starting Charity Nepal Backend deployment..."
    
    install_uv
    setup_environment
    run_migrations
    collect_static
    
    log_success "Deployment completed successfully!"
    log_info "You can now start the server using: ./deploy.sh dev or ./deploy.sh prod"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "dev")
        start_dev_server
        ;;
    "prod")
        start_prod_server
        setup_celery
        ;;
    "docker")
        setup_docker
        ;;
    "test")
        run_tests
        ;;
    "test-api")
        test_api
        ;;
    "migrate")
        run_migrations
        ;;
    "superuser")
        create_superuser
        ;;
    "collect-static")
        collect_static
        ;;
    "ssl")
        generate_ssl
        ;;
    "backup")
        backup_database
        ;;
    "status")
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "help"|"-h"|"--help")
        echo "Charity Nepal Backend Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy        Full deployment setup (default)"
        echo "  dev           Start development server"
        echo "  prod          Start production server with Celery"
        echo "  docker        Setup and run with Docker"
        echo "  test          Run test suite"
        echo "  test-api      Run API integration tests"
        echo "  migrate       Run database migrations"
        echo "  superuser     Create superuser account"
        echo "  collect-static Collect static files"
        echo "  ssl           Generate SSL certificate"
        echo "  backup        Backup database"
        echo "  status        Show system status"
        echo "  stop          Stop all services"
        echo "  help          Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use '$0 help' to see available commands"
        exit 1
        ;;
esac
