#!/bin/bash

################################################################################
# BankAi Enterprise Deployment Script
# This script automates the deployment of BankAi to an isolated data center
#
# Usage: sudo ./deploy.sh [OPTIONS]
# Options:
#   -h, --help              Show this help message
#   -e, --env FILE          Use custom environment file (default: .env.production)
#   --skip-docker           Skip Docker installation (assumes already installed)
#   --skip-models           Skip local model readiness checks
#   --no-ssl                Deploy without SSL (development only)
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="bankai"
APP_HOME="/data/bankai"
ENV_FILE="${SCRIPT_DIR}/.env.production"
SKIP_DOCKER=false
SKIP_MODELS=false
NO_SSL=true

# Functions
print_header() {
    echo -e "\n${BLUE}═════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Could not detect OS"
        exit 1
    fi

    . /etc/os-release
    print_info "Detected OS: $PRETTY_NAME"
}

show_help() {
    grep "^#" "$0" | grep -E "^\s*#\s+[^#]" | sed 's/^#\s*//'
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-models)
                SKIP_MODELS=true
                shift
                ;;
            --no-ssl)
                NO_SSL=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

install_docker() {
    if $SKIP_DOCKER; then
        print_info "Skipping Docker installation"
        return
    fi

    print_header "Installing Docker"

    if command -v docker &> /dev/null; then
        print_success "Docker already installed: $(docker --version)"
        return
    fi

    apt-get update
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    systemctl start docker
    systemctl enable docker

    print_success "Docker installed successfully"
}

install_docker_compose() {
    print_header "Installing Docker Compose"

    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose already installed: $(docker-compose --version)"
        return
    fi

    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K[^"]+')
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    print_success "Docker Compose installed successfully"
}

setup_application_user() {
    print_header "Setting up application user and directories"

    if id "$APP_USER" &>/dev/null; then
        print_info "User $APP_USER already exists"
    else
        useradd -m -s /bin/bash $APP_USER
        print_success "Created user: $APP_USER"
    fi

    # Add user to docker group
    usermod -aG docker $APP_USER

    # Create directories
    mkdir -p $APP_HOME
    mkdir -p $APP_HOME/uploads
    mkdir -p $APP_HOME/backups
    mkdir -p $APP_HOME/certs
    mkdir -p $APP_HOME/logs

    # Set permissions
    chown -R $APP_USER:$APP_USER $APP_HOME
    chmod -R 755 $APP_HOME

    print_success "Application directories created"
}

copy_application_files() {
    print_header "Copying application files"

    if [[ ! -d "$SCRIPT_DIR/backend" ]]; then
        print_error "Backend directory not found at $SCRIPT_DIR/backend"
        exit 1
    fi

    if [[ ! -d "$SCRIPT_DIR/frontend" ]]; then
        print_error "Frontend directory not found at $SCRIPT_DIR/frontend"
        exit 1
    fi

    # Copy all application files
    cp -r $SCRIPT_DIR/backend $APP_HOME/
    cp -r $SCRIPT_DIR/frontend $APP_HOME/
    cp $SCRIPT_DIR/docker-compose.yml $APP_HOME/
    cp $SCRIPT_DIR/nginx.conf $APP_HOME/

    # Copy environment file
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" $APP_HOME/.env
        print_success "Environment file copied from $ENV_FILE"
    else
        print_warning "Environment file not found at $ENV_FILE"
        print_info "Creating default .env file..."
        cp $SCRIPT_DIR/.env.production $APP_HOME/.env
    fi

    chown -R $APP_USER:$APP_USER $APP_HOME

    print_success "Application files copied to $APP_HOME"
}

build_images() {
    print_header "Building Docker images"

    cd $APP_HOME

    # Build backend image
    print_info "Building backend image..."
    docker-compose build backend

    # Build frontend image
    print_info "Building frontend image..."
    docker-compose build frontend

    print_success "Docker images built successfully"
}

start_services() {
    print_header "Starting services"

    cd $APP_HOME

    # Start all services
    docker-compose up -d

    # Wait for services to be ready
    print_info "Waiting for services to start..."
    sleep 10

    # Check service status
    docker-compose ps

    print_success "Services started successfully"
}

init_database() {
    print_header "Initializing database"

    cd $APP_HOME

    # Wait for database to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 5

    # Run migrations
    print_info "Running database migrations..."
    docker-compose exec -T backend alembic upgrade head

    print_success "Database initialized successfully"
}

verify_local_models() {
    if $SKIP_MODELS; then
        print_warning "Skipping local model readiness checks (--skip-models)"
        print_warning "vLLM model weights must be present before AI responses can work"
        return
    fi

    print_header "Checking local vLLM models"

    cd $APP_HOME

    print_info "Checking vLLM service status..."
    docker-compose ps vllm-b vllm-c || true

    print_success "Local model services checked"
}

verify_installation() {
    print_header "Verifying installation"

    cd $APP_HOME

    # Check services
    print_info "Checking service status..."
    if docker-compose ps | grep -q "Up"; then
        print_success "All services are running"
    else
        print_error "Some services are not running"
        docker-compose ps
        return 1
    fi

    # Test API
    print_info "Testing API health endpoint..."
    if curl -s http://localhost/api/health > /dev/null; then
        print_success "API is responding"
    else
        print_warning "API not responding (may still be initializing)"
    fi

    # Show service ports
    print_info "Service endpoints:"
    echo "  Frontend:  http://localhost"
    echo "  API:       http://localhost/api"
    echo "  MinIO:     http://localhost:9001"
    echo "  Qdrant:    http://localhost:6333"
}

print_summary() {
    print_header "Deployment Complete!"

    echo -e "${GREEN}BankAi Enterprise has been successfully deployed!${NC}\n"

    echo "Next steps:"
    echo "  1. Change default credentials in $APP_HOME/.env"
    echo "  2. Visit http://$(hostname -I | awk '{print $1}') to access the UI"
    echo "  3. Login with: admin@bankai.io / admin123"
    echo "  4. Change admin password immediately!"
    echo "  5. Read DEPLOYMENT_GUIDE.md for post-deployment configuration"
    echo ""
    echo "For production deployment:"
    echo "  1. Configure SSL/TLS certificates"
    echo "  2. Update firewall rules"
    echo "  3. Set up monitoring and backup"
    echo "  4. Configure audit logging"
    echo ""
    echo "Deployment logs are saved to: $APP_HOME/logs/"
    echo ""
}

# Main execution
main() {
    parse_args "$@"
    check_root
    check_os

    print_header "BankAi Enterprise Deployment"
    print_info "Starting deployment at $(date)"

    install_docker
    install_docker_compose
    setup_application_user
    copy_application_files
    build_images
    start_services
    init_database

    if [ "$SKIP_MODELS" = false ]; then
        verify_local_models
    fi

    verify_installation
    print_summary

    print_info "Deployment completed at $(date)"
}

# Run main function
main "$@"
