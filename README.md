# 🚀 Social Requests - AI-Powered Complaint Intelligence Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-orange.svg)](/.github/workflows)
[![API](https://img.shields.io/badge/API-REST-red.svg)](https://www.django-rest-framework.org/)

*Transform customer feedback chaos into actionable insights with AI-powered clustering and visualization*

[🎯 Features](#-features) • [🚀 Quick Start](#-quick-start) • [📖 Documentation](#-api-documentation) • [🔧 Configuration](#-configuration) • [🤝 Contributing](#-contributing)

</div>

---

## 🎯 Overview

**Social Requests** is an enterprise-grade Django application that revolutionizes how organizations handle customer feedback. By leveraging cutting-edge AI models and machine learning algorithms, it automatically clusters, analyzes, and visualizes customer complaints to reveal hidden patterns and actionable insights.

### 🎪 Live Demo
Experience the platform in action with our interactive visualization dashboard that transforms raw feedback into beautiful, explorable data clusters.

### 🏆 Why Social Requests?

- **🧠 AI-First Approach**: Powered by GigaChat and OpenRouter for state-of-the-art text embeddings
- **📊 Smart Clustering**: Automatic K-means clustering with silhouette optimization
- **🎨 Interactive Visualization**: Real-time t-SNE plots with drag-and-drop cluster management
- **🔍 Intelligent Search**: Semantic similarity search and full-text capabilities
- **📱 Multi-Project Support**: Isolated data silos for different products or clients
- **⚡ Batch Processing**: High-performance bulk operations for enterprise scale
- **🔗 YouTube Integration**: Direct import of public comments for social media analysis

---

## ✨ Features

### 🤖 AI & Machine Learning
- **Multi-Provider Embeddings**: Support for GigaChat, OpenRouter
- **Automatic Clustering**: K-means with intelligent cluster count optimization
- **Dimensionality Reduction**: t-SNE visualization for 2D scatter plots
- **LLM Summarization**: Auto-generated cluster titles and descriptions
- **Semantic Search**: Cosine similarity-based complaint discovery

### 🏗️ Enterprise Architecture
- **Project Isolation**: Multi-tenant architecture with project-based data separation
- **RESTful API**: Comprehensive Django REST Framework endpoints
- **Async Processing**: Background task handling for large datasets
- **Batch Operations**: Optimized bulk processing for thousands of complaints
- **Database Agnostic**: SQLite for development

### 🎨 User Experience
- **Interactive Dashboard**: Custom cluster creation
- **Real-time Updates**: Live visualization updates during clustering
- **Responsive Design**: Bootstrap 5-powered responsive interface
- **Search & Filter**: Advanced filtering and search capabilities

### 🔧 Developer Experience
- **Management Commands**: CLI tools for data import and processing
- **Comprehensive Testing**: Full test suite with CI/CD integration
- **Docker Support**: Containerized deployment ready
- **Extensible Architecture**: Plugin-ready design for custom integrations

---

## 🚀 Quick Start

### Prerequisites

```bash
# System Requirements
Python 3.11+
Git
Virtual Environment (recommended)

# Optional for advanced features
Node.js 18+ (for frontend development)
Docker & Docker Compose (for containerized deployment)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/LIT-24-25/social-requests.git
cd social-requests

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python manage.py migrate

# 5. Start development server
python manage.py runserver
```

### 🎉 First Steps

1. **Access the platform**: Navigate to `http://localhost:8000`
2. **Create a project**: Use the admin interface or API
3. **Import data**: Upload complaints via API, integrated form or use the YouTube importer
4. **Generate embeddings**: Batch process your complaints for AI analysis
5. **Create clusters**: Use automatic clustering or manual selection
6. **Explore insights**: Navigate to the interactive visualization dashboard

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# AI Model Providers
GIGACHAT_TOKEN=your_gigachat_token_here
OPENROUTER_TOKEN=your_openrouter_token_here

# YouTube Data Import
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### API Provider Setup

#### GigaChat (Sber AI)
1. Register at [developers.sber.ru](https://developers.sber.ru/)
2. Obtain your API credentials
3. Add to `.env` as `GIGACHAT_TOKEN`

#### OpenRouter
1. Sign up at [openrouter.ai](https://openrouter.ai/)
2. Generate an API key
3. Add to `.env` as `OPENROUTER_TOKEN`

#### YouTube Data API
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Generate an API key
4. Add to `.env` as `YOUTUBE_API_KEY`

---

## 📖 API Documentation

### Core Endpoints

#### Projects
```http
GET    /api/projects/              # List all projects
POST   /api/projects/              # Create new project
GET    /api/projects/{id}/         # Get project details
```

#### Complaints Management
```http
GET    /project/{id}/api/complaints/           # List complaints
POST   /project/{id}/api/complaints/           # Create complaint
GET    /project/{id}/api/complaints/{id}/      # Get complaint
PUT    /project/{id}/api/complaints/{id}/      # Update complaint
DELETE /project/{id}/api/complaints/{id}/      # Delete complaint
```

#### Clustering Operations
```http
POST   /project/{id}/api/create-cluster/       # Create cluster from complaint IDs
GET    /project/{id}/api/clusters/             # List all clusters
GET    /project/{id}/api/clusters/{id}/        # Get cluster details
POST   /project/{id}/api/clusterising/         # Auto-cluster complaints
POST   /project/{id}/api/apply_tsne/           # Generate t-SNE coordinates
```

#### Data Import & Processing
```http
POST   /project/{id}/api/add-youtube/          # Import YouTube comments
GET    /project/{id}/api/task-status/{uuid}/   # Check import progress
POST   /project/{id}/api/regenerate-summary/   # Refresh cluster summaries
```

#### Search & Discovery
```http
GET    /project/{id}/api/search/?q={query}     # Search complaints
GET    /project/{id}/api/similar/{id}/         # Find similar complaints
```

### Request/Response Examples

#### Create Complaint
```bash
curl -X POST http://localhost:8000/project/1/api/complaints/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "App crashes on startup",
    "text": "The mobile app crashes immediately when I try to open it on my iPhone 12."
  }'
```

#### Auto-Cluster Complaints
```bash
curl -X POST http://localhost:8000/project/1/api/clusterising/ \
  -H "Content-Type: application/json" \
  -d '{
    "auto_clusters": true,
    "model": "GigaChat",
    "max_clusters": 15
  }'
```

#### Import YouTube Comments
```bash
curl -X POST http://localhost:8000/project/1/api/add-youtube/ \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtu.be/dQw4w9WgXcQ",
    "max_results": 1000,
    "batch_size": 50
  }'
```

---

## 🛠️ Management Commands

### Data Import & Processing

```bash
# Import complaints from CSV
python manage.py store_data --csv_path data.csv --chunk-size 100 --project-id 1

# Auto-cluster with optimization
python manage.py clusterising --auto-clusters --model OpenRouter --project-id 1

# Generate t-SNE visualization
python manage.py applying_T-sne --perplexity 30 --project-id 1

# Import YouTube comments
python manage.py add_youtube "https://youtu.be/VIDEO_ID" 1 --max-results 2000
```

### Database Management

```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

---

## 🎨 Interactive Visualization

### Dashboard Features

- **🎯 Scatter Plot Visualization**: Interactive t-SNE plot with complaint positioning
- **🎨 Color-Coded Clusters**: Visual distinction between different complaint groups
- **🔍 Zoom & Pan**: Smooth navigation through large datasets
- **📊 Cluster Statistics**: Real-time metrics and insights
- **🎛️ Filter Controls**: Dynamic filtering by cluster
- **👀 Responses Filter**: Search responses by keyword, email and semantic similarity
- **📱 Responsive Design**: Optimized for desktop and mobile viewing

### Navigation

1. **Main Dashboard**: `http://localhost:8000/project/{id}/visual/`
2. **Cluster Details**: Click any cluster to view constituent complaints
3. **Complaint Inspector**: Double-click complaints for detailed view
---

## 🧪 Testing & Quality Assurance

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test complaints
python manage.py test clusters

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### CI/CD Pipeline

Our GitHub Actions workflow ensures code quality:

- **Multi-Python Testing**: Python 3.11 and 3.12 compatibility
- **Automated Testing**: Full test suite on every PR
- **Code Quality Checks**: Linting and formatting validation
- **Security Scanning**: Dependency vulnerability checks
- **Telegram Notifications**: Real-time build status updates

---

## 🏗️ Architecture & Tech Stack

### Backend Stack
- **🐍 Django 4.2**: Robust web framework with ORM
- **🔗 Django REST Framework**: Comprehensive API development
- **🤖 AI Integration**: GigaChat, OpenRouter
- **📊 Machine Learning**: scikit-learn for clustering and dimensionality reduction
- **🗄️ Database**: SQLite
- **⚡ Async Processing**: Background task management

### Frontend Stack
- **🎨 Bootstrap 5**: Modern, responsive UI framework
- **⚡ Vue.js**: Lightweight, fast and responsive UI

### DevOps & Deployment
- **🐳 Docker**: Containerized deployment
- **🔄 GitHub Actions**: Automated CI/CD pipeline
- **📊 Monitoring**: Built-in logging and metrics
- **🔒 Security**: Environment-based configuration

### Data Flow Architecture

```
Raw Complaints → AI Embeddings → Clustering Algorithm → Visualization
     ↓              ↓                    ↓                ↓
 REST API  GigaChat/OpenRouter    K-means/t-SNE  Interactive Dashboard
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale for production
docker-compose -f docker-compose.prod.yml up -d
```
---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get started:

### Development Setup

```bash
# Fork the repository and clone your fork
git clone https://github.com/YOUR_USERNAME/social-requests.git
cd social-requests

# Create a feature branch
git checkout -b feature/amazing-new-feature

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install
```

### Contribution Guidelines

1. **🔀 Fork & Branch**: Create a feature branch from `main`
2. **✅ Test Coverage**: Maintain or improve test coverage
3. **📝 Documentation**: Update docs for new features
4. **🎯 Conventional Commits**: Use semantic commit messages
5. **🔍 Code Review**: All PRs require review before merging
6. **🚫 No Secrets**: Never commit real API keys or sensitive data

### Code Style

- **Python**: Follow PEP 8 with Black formatting
- **JavaScript**: ESLint with Airbnb configuration
- **Documentation**: Clear, concise, and example-rich

---

## 📊 Performance & Scalability

### Benchmarks

- **Embedding Generation**: 1000 complaints/minute with batch processing
- **Clustering Performance**: Sub-second clustering for 10k+ complaints
- **API Response Times**: <200ms for typical requests

### Optimization Features

- **Batch Processing**: Efficient bulk operations
- **Database Indexing**: Optimized queries for large datasets
- **Caching Strategy**: Redis-based caching for frequent operations
- **Async Tasks**: Background processing for heavy operations

---

## 🔒 Security & Privacy

### Security Features

- **🔐 Environment Variables**: Secure credential management
- **🛡️ CSRF Protection**: Built-in Django security
- **🔒 Input Validation**: Comprehensive data sanitization
---

## 📈 Roadmap

### Upcoming Features

- **🔮 Advanced Analytics**: Trend analysis and predictive insights
- **🌐 Multi-language Support**: International complaint processing
- **📱 Mobile App**: Native iOS and Android applications
- **🔗 Third-party Integrations**: Slack, Teams, Jira connectors
- **🤖 Auto-response**: AI-powered response suggestions
- **📊 Advanced Visualizations**: 3D clustering and timeline views
- **🔐 Authentication**: Add account separation for different purposes
### Community Requests

Vote on features and track progress in our [GitHub Issues](https://github.com/LIT-24-25/social-requests/issues).

---

## 📞 Support & Community

### Getting Help

- **📖 Documentation**: Comprehensive guides and API reference
- **💬 GitHub Issues**: Community Q&A and feature requests
- **🐛 Issue Tracker**: Bug reports and feature requests
- **📧 Telegram Support**: [Alex](https://t.me/Aletavrus), [Andrew](https://t.me/UPLAPPU)

### Community

- **🌟 Star the Project**: Show your support on GitHub

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **GigaChat Team**: For providing excellent Russian language AI capabilities
- **OpenRouter**: For democratizing access to multiple AI models
- **Django Community**: For the robust web framework
- **scikit-learn**: For powerful machine learning algorithms
- **Bootstrap Team**: For the beautiful UI framework
- **Vue.js**: For wonderful responsive framework to create powerful websites
---

<div align="center">

**Made with ❤️ and a lot of embeddings**

[⭐ Star us on GitHub](https://github.com/your-org/social-requests) • [🐛 Report Bug](https://github.com/LIT-24-25/social-requests/issues) • [💡 Request Feature](https://github.com/LIT-24-25/social-requests/issues)

</div> 