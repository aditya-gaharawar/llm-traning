#!/bin/bash
#
# LLM Trainer GitHub Setup Script
#
# This script initializes a Git repository for the LLM Trainer application,
# adds all files, creates an initial commit, and prepares for GitHub push.
#
# Usage: ./setup_github.sh [project_directory]
#
# If no project directory is provided, the script will use the current directory.
#

set -e  # Exit on error

# Default project directory
PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"
CURRENT_DIR=$(pwd)

echo "==================================================================="
echo "🚀 LLM Trainer GitHub Setup"
echo "==================================================================="
echo "Setting up Git repository in: $CURRENT_DIR"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed. Please install Git first."
    echo "   Visit: https://git-scm.com/downloads"
    exit 1
fi

# Check if directory is already a git repository
if [ -d ".git" ]; then
    echo "⚠️  Warning: Git repository already exists in this directory."
    read -p "Do you want to reinitialize? This will reset all Git history. (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Operation canceled."
        exit 0
    fi
    rm -rf .git
    echo "Removed existing .git directory."
fi

# Initialize git repository
echo "📁 Initializing Git repository..."
git init

# Create .gitignore file if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore file..."
    cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
.hypothesis/
.pytest_cache/

# Node.js/Frontend
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log
frontend/build/
frontend/dist/
frontend/.env.local
frontend/.env.development.local
frontend/.env.test.local
frontend/.env.production.local

# Environment variables
.env
.env.local
.env.development
.env.test
.env.production
*.env

# Database
*.sqlite
*.sqlite3
*.db
postgres-data/
redis-data/

# ML models and artifacts
models/
datasets/
*.pt
*.pth
*.safetensors
*.bin
*.gguf
*.onnx
cache/
artifacts/
tensorboard/

# Logs and monitoring
logs/
*.log
prometheus-data/
grafana-data/

# Uploads
uploads/
media/

# IDE specific files
.idea/
.vscode/
*.swp
*.swo
.DS_Store
.project
.classpath
.c9/
*.launch
.settings/
*.sublime-workspace
*.sublime-project

# Docker
.dockerignore

# Alembic migrations (keep the directory structure)
alembic/versions/*.py
!alembic/versions/__init__.py

# Misc
.directory
*.tmp
*.bak
*.swp
*~.nib
local.properties
EOL
fi

# Create a README.md if it doesn't exist
if [ ! -f "README.md" ]; then
    echo "📝 Creating README.md file..."
    cat > README.md << 'EOL'
# LLM Trainer

A comprehensive web application for training and fine-tuning Large Language Models (LLMs) with a focus on Unsloth integration.

## Features

- **Model Management**: Upload, download, and manage models from HuggingFace Hub
- **Dataset Handling**: Process and prepare datasets for training
- **Training Configuration**: Configure training parameters for SFT, LoRA, GRPO, DPO
- **Real-time Monitoring**: Track training progress with TensorBoard integration
- **Web Interface**: Modern React frontend for easy management

## Quick Start

```bash
# Development setup
docker compose --profile dev up -d

# Production deployment
docker compose --profile prod up -d

# Database setup with sample data
python scripts/setup_db.py --sample-data
```

## Access Points

- **API**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **TensorBoard**: http://localhost:6006

## License

MIT
EOL
fi

# Check if project structure exists, create if not
echo "🔍 Checking project structure..."
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "📂 Creating project directory structure..."
    
    # Create main project directories
    mkdir -p backend/api/endpoints
    mkdir -p backend/core
    mkdir -p backend/db
    mkdir -p backend/models
    mkdir -p backend/schemas
    mkdir -p backend/utils
    mkdir -p frontend/src/pages
    mkdir -p frontend/src/components
    mkdir -p scripts
    mkdir -p alembic/versions
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning/dashboards
    mkdir -p monitoring/grafana/provisioning/datasources
    
    # Create placeholder files to ensure directories are committed
    touch backend/api/endpoints/__init__.py
    touch backend/api/__init__.py
    touch backend/core/__init__.py
    touch backend/db/__init__.py
    touch backend/models/__init__.py
    touch backend/schemas/__init__.py
    touch backend/utils/__init__.py
    touch backend/__init__.py
    touch alembic/versions/.gitkeep
    touch frontend/src/pages/.gitkeep
    touch frontend/src/components/.gitkeep
    touch monitoring/prometheus/.gitkeep
    touch monitoring/grafana/provisioning/dashboards/.gitkeep
    touch monitoring/grafana/provisioning/datasources/.gitkeep
    
    echo "✅ Project structure created."
fi

# Add all files to git
echo "➕ Adding files to git staging..."
git add .

# Commit changes
echo "💾 Creating initial commit..."
git commit -m "Initial commit: LLM Trainer application with FastAPI backend and React frontend"

# Instructions for GitHub
echo ""
echo "==================================================================="
echo "🎉 Git repository initialized successfully!"
echo "==================================================================="
echo ""
echo "To push to GitHub, follow these steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Connect your local repository to GitHub:"
echo "   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git"
echo ""
echo "3. Push your code to GitHub:"
echo "   git push -u origin main"
echo ""
echo "==================================================================="

# Make the script executable
chmod +x "$0"

echo "Setup complete! Your LLM Trainer project is ready for GitHub."
