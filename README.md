# Charity Nepal Backend - Complete Documentation

## 🎯 Project Overview

The Charity Nepal Backend is a comprehensive Django REST API system for managing charity campaigns, donations, and providing intelligent recommendations using machine learning algorithms. The system supports secure authentication, payment integration, and advanced analytics.

## 🏗️ Architecture

### System Components

- **Django 5.2.5** - Web framework
- **Django REST Framework** - API development
- **JWT Authentication** - Secure user authentication
- **SQLite** - Database (development)
- **Redis** - Caching and Celery broker
- **Celery** - Background task processing
- **ML Algorithms** - Recommendation system
- **UV** - Modern Python package management

### Applications Structure

```
charity_backend/
├── users/          # User management and authentication
├── cases/          # Charity cases management
├── donations/      # Donation processing
├── payments/       # Payment integration ( /Khalti)
├── recommendations/ # ML-powered recommendation system
└── charity_backend/ # Main project configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- Redis server
- Git

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd charity_nepal
```

2. **Run automated deployment:**

```bash
./deploy.sh deploy
```

3. **Create superuser:**

```bash
./deploy.sh superuser
```

4. **Start development server:**

```bash
./deploy.sh dev
```

### Alternative Manual Setup

1. **Install UV:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Initialize project:**

```bash
uv init
uv sync
```

3. **Run migrations:**

```bash
uv run python manage.py migrate
```

4. **Start server:**

```bash
uv run python manage.py runserver
```

## 📚 API Documentation

### Base URL

```
Development: http://127.0.0.1:8000/api/
Production: https://your-domain.com/api/
```

### Authentication

All protected endpoints require JWT token authentication:

```http
Authorization: Bearer <access_token>
```

### Core Endpoints

#### Authentication (`/api/auth/`)

- `POST /register/` - User registration
- `POST /login/` - User login
- `POST /logout/` - User logout
- `POST /refresh/` - Refresh JWT token
- `GET /profile/` - Get user profile
- `PUT /profile/` - Update user profile

#### Cases (`/api/cases/`)

- `GET /` - List all cases (with pagination)
- `POST /` - Create new case (authenticated)
- `GET /{id}/` - Get case details
- `PUT /{id}/` - Update case (owner/admin)
- `DELETE /{id}/` - Delete case (owner/admin)
- `GET /categories/` - Get available categories
- `GET /search/` - Search cases with filters

#### Donations (`/api/donations/`)

- `GET /` - List user donations (authenticated)
- `POST /` - Create donation (authenticated)
- `GET /{id}/` - Get donation details
- `GET /statistics/` - Get donation statistics (admin)

#### Payments (`/api/payments/`)

- `POST /create-intent/` - Create payment intent
- `GET /intent/{id}/` - Get payment status
- `POST / /verify/` - Verify   payment
- `POST /khalti/verify/` - Verify Khalti payment

#### Recommendations (`/api/recommendations/`)

- `GET /personal/` - Get personalized recommendations
- `GET /trending/` - Get trending cases
- `GET /profile/` - Get/update recommendation profile
- `GET /history/` - Get recommendation history
- `POST /track/` - Track recommendation interactions

#### Health Checks

- `GET /api/health/` - System health status
- `GET /api/ready/` - Readiness check
- `GET /api/live/` - Liveness check

## 🤖 Machine Learning Features

### Recommendation Algorithms

1. **Content-Based Filtering**

   - Analyzes case descriptions using TF-IDF
   - Recommends similar cases based on content

2. **Collaborative Filtering**

   - Uses user-item interaction matrix
   - Finds similar users and their preferences

3. **Clustering-Based Recommendations**

   - K-means clustering of donor profiles
   - Recommends popular cases within clusters

4. **Decision Tree Classifier**

   - Predicts donation likelihood
   - Based on user behavior patterns

5. **Fraud Detection**

   - Naive Bayes classifier for suspicious activities
   - Analyzes donation patterns

6. **Hybrid System**
   - Combines multiple algorithms
   - Weighted scoring for best results

### Usage Examples

```python
# Get personalized recommendations
GET /api/recommendations/personal/?count=10&algorithm=hybrid

# Get similar cases
GET /api/recommendations/similar/123/?count=5

# Track recommendation interaction
POST /api/recommendations/track/
{
    "recommendation_id": 456,
    "action": "click"
}
```

## 💳 Payment Integration

### Supported Payment Gateways

1. ** **

   - Merchant authentication
   - Transaction verification
   - Callback handling

2. **Khalti**
   - Digital wallet integration
   - Real-time verification
   - Webhook support

### Payment Flow

1. **Create Payment Intent:**

```python
POST /api/payments/create-intent/
{
    "donation_id": 123,
    "payment_method": " "
}
```

2. **Process Payment:**

   - User redirected to payment gateway
   - Payment processed externally

3. **Verify Payment:**

```python
POST /api/payments/ /verify/
{
    "payment_intent_id": 456,
    "transaction_code": "abc123"
}
```

## 🔄 Background Tasks (Celery)

### Implemented Tasks

1. **Email Notifications**

   - Donation confirmations
   - Case approvals
   - Milestone updates

2. **Data Processing**

   - Update collected amounts
   - Generate analytics reports
   - Process pending donations

3. **ML Model Management**
   - Retrain recommendation models
   - Update user profiles
   - Clean up old data

### Running Celery

```bash
# Start Celery worker
celery -A charity_backend worker --loglevel=info

# Start Celery beat scheduler
celery -A charity_backend beat --loglevel=info

# Monitor with Flower
celery -A charity_backend flower
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Included

- **web** - Django application
- **redis** - Cache and message broker
- **worker** - Celery worker
- **beat** - Celery scheduler
- **flower** - Task monitoring

## 🧪 Testing

### Running Tests

```bash
# Run all tests
./deploy.sh test

# Run Django unit tests
uv run python manage.py test

# Run API integration tests
./deploy.sh test-api

# Run custom test suite
uv run python run_tests.py
```

### Test Coverage

- **Unit Tests** - Model and utility functions
- **API Tests** - Endpoint functionality
- **Integration Tests** - End-to-end workflows
- **ML Tests** - Algorithm performance

## 📊 Monitoring & Analytics

### Health Monitoring

```bash
# Check system status
./deploy.sh status

# Health check endpoint
curl http://localhost:8000/api/health/
```

### Analytics Features

1. **Donation Analytics**

   - Total donations per category
   - Top donors and recipients
   - Conversion rates

2. **Recommendation Analytics**

   - Algorithm performance
   - Click-through rates
   - User engagement metrics

3. **System Metrics**
   - Database performance
   - Cache hit rates
   - Background task status

## 🔧 Configuration

### Environment Variables

```bash
# Core Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment Gateways
 _MERCHANT_ID=your- -merchant-id
 _SECRET_KEY=your- -secret-key
KHALTI_SECRET_KEY=your-khalti-secret-key

# Machine Learning
ML_MODEL_PATH=/path/to/models/
RECOMMENDATION_CACHE_TIMEOUT=3600
```

### Database Settings

```python
# Development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Production (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'charity_nepal',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔐 Security Features

### Implemented Security Measures

1. **Authentication & Authorization**

   - JWT token-based authentication
   - Role-based permissions (donor/admin)
   - Password validation and hashing

2. **API Security**

   - CORS configuration
   - Rate limiting
   - Input validation and sanitization

3. **Data Protection**

   - Encrypted sensitive data
   - Secure payment processing
   - Privacy controls for donations

4. **Infrastructure Security**
   - HTTPS enforcement
   - Security headers
   - Environment variable protection

## 📈 Performance Optimization

### Caching Strategy

1. **Redis Caching**

   - Query result caching
   - Session storage
   - Recommendation caching

2. **Database Optimization**

   - Query optimization
   - Index usage
   - Connection pooling

3. **API Performance**
   - Pagination for large datasets
   - Selective field retrieval
   - Background task processing

## 🚨 Troubleshooting

### Common Issues

1. **Server Won't Start**

```bash
# Check for port conflicts
lsof -i :8000

# Verify dependencies
uv run python -c "import django; print(django.VERSION)"

# Check database migrations
uv run python manage.py showmigrations
```

2. **Celery Issues**

```bash
# Check Redis connection
redis-cli ping

# Verify Celery configuration
celery -A charity_backend inspect active
```

3. **Database Issues**

```bash
# Reset database
rm db.sqlite3
uv run python manage.py migrate

# Create test data
uv run python manage.py loaddata fixtures/initial_data.json
```

### Debug Mode

Enable detailed logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch:** `git checkout -b feature/amazing-feature`
3. **Make changes and commit:** `git commit -m 'Add amazing feature'`
4. **Push to branch:** `git push origin feature/amazing-feature`
5. **Create Pull Request**

### Code Standards

- **Python:** Follow PEP 8 guidelines
- **Django:** Use Django best practices
- **API:** RESTful design principles
- **Tests:** Maintain test coverage above 80%

## 📞 Support

### Getting Help

1. **Documentation** - Check this README and code comments
2. **Issues** - Create GitHub issue for bugs
3. **Discussions** - Use GitHub discussions for questions
4. **Email** - Contact project maintainers

### Deployment Support

```bash
# Full deployment help
./deploy.sh help

# System status check
./deploy.sh status

# Emergency stop
./deploy.sh stop
```

---

## 📋 Project Checklist

### ✅ Completed Features

- [x] User authentication and authorization
- [x] Charity case management (CRUD)
- [x] Donation processing system
- [x] Payment gateway integration ( /Khalti)
- [x] ML-powered recommendation system
- [x] Background task processing (Celery)
- [x] Admin interface with analytics
- [x] API documentation and testing
- [x] Docker containerization
- [x] Health monitoring
- [x] Security implementation
- [x] Automated deployment scripts

### 🔄 In Progress

- [ ] Real-time notifications (WebSocket)
- [ ] Advanced fraud detection
- [ ] Mobile app API optimization
- [ ] Performance monitoring dashboard

### 📋 Future Enhancements

- [ ] Multi-language support (i18n)
- [ ] Advanced analytics dashboard
- [ ] Social media integration
- [ ] Blockchain donation tracking
- [ ] AI-powered case verification

---

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Maintainer:** Charity Nepal Development Team
