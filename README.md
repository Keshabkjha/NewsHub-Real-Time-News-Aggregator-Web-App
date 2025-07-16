<div align="center">
  <h1>📰 NewsHub</h1>
  <h3>Real-Time News Aggregator Web Application</h3>
  
  [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
  [![Django](https://img.shields.io/badge/Django-4.2-092E20.svg?logo=django)](https://www.djangoproject.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![GitHub stars](https://img.shields.io/github/stars/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App?style=social)](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/stargazers)
  [![GitHub forks](https://img.shields.io/github/forks/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App?style=social)](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/network/members)
  [![GitHub issues](https://img.shields.io/github/issues/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App)](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/issues)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
</div>

## 🚀 About NewsHub

NewsHub is a modern, real-time news aggregation platform that brings together the latest news from multiple sources into one convenient location. Built with Django, Django REST Framework, and modern JavaScript, NewsHub provides a seamless experience for users to stay updated with current events.

### 🌟 Key Features

- **Real-time News Aggregation**: Get the latest news from multiple sources in real-time
- **Personalized Feed**: Customize your news feed based on your interests
- **Push Notifications**: Stay updated with breaking news alerts
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **User Authentication**: Secure signup and login system
- **Bookmarking**: Save articles to read later
- **Advanced Search**: Find news articles with powerful search capabilities
- **Dark Mode**: Easy on the eyes with dark theme support

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.2
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Caching**: Redis
- **Task Queue**: Celery
- **Search**: Django Haystack with Whoosh
- **Authentication**: JWT & Session-based
- **Real-time**: Django Channels & WebSockets

### Frontend
- **HTML5** & **CSS3**
- **JavaScript (ES6+)**
- **TailwindCSS** for styling
- **Alpine.js** for interactivity
- **HTMX** for dynamic content
- **Service Workers** for offline support

### DevOps
- **Docker** & **Docker Compose**
- **Nginx** as reverse proxy
- **Gunicorn** as WSGI server
- **GitHub Actions** for CI/CD
- **Sentry** for error tracking
- **PostgreSQL** for production database

## Tech Stack

- **Backend**: Django 4.2
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), TailwindCSS
- **Database**: PostgreSQL
- **Caching**: Redis
- **Task Queue**: Celery
- **Search**: Django Haystack with Whoosh
- **Real-time**: WebSockets with Django Channels
- **Deployment**: Docker, Nginx, Gunicorn

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ & npm 8+
- Git

### 🛠️ Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App.git
   cd NewsHub-Real-Time-News-Aggregator-Web-App
   ```

2. **Set up Python virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Unix or MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up the database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Start the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Frontend: http://localhost:8000
   - Admin: http://localhost:8000/admin

### 🐳 Docker Setup (Alternative)

1. **Build and start containers**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

3. **Access the application**
   - Frontend: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 📁 Project Structure

```
NewsHub-Real-Time-News-Aggregator-Web-App/
├── .github/                  # GitHub workflows and templates
├── config/                   # Project configuration (settings, URLs, WSGI, ASGI)
│   ├── settings/
│   │   ├── base.py          # Base settings
│   │   ├── development.py   # Development settings
│   │   └── production.py    # Production settings
│   ├── urls/
│   └── asgi.py & wsgi.py
│
├── newshub/                  # Main app
│   ├── migrations/
│   ├── static/
│   ├── templates/
│   ├── tests/
│   ├── admin.py
│   ├── apps.py
│   └── models.py
│
├── accounts/                 # User authentication & management
│   ├── migrations/
│   ├── templates/
│   ├── tests/
│   └── ...
│
├── aggregator/               # News aggregation logic
│   ├── management/
│   ├── migrations/
│   ├── tests/
│   └── ...
│
├── notifications/            # Notification system
│   ├── migrations/
│   ├── templatetags/
│   └── ...
│
├── frontend/                 # Frontend assets
│   ├── src/
│   │   ├── js/
│   │   └── scss/
│   ├── static/
│   └── package.json
│
├── requirements/             # Python requirements
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── manage.py
└── README.md
```

## ⚙️ Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Django
# ======
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
# ========
DATABASE_URL=postgres://user:password@localhost:5432/newshub

# Redis
# =====
REDIS_URL=redis://localhost:6379/0

# Email
# =====
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=news@newshub.example.com

# AWS (for production)
# ===================
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_DEFAULT_ACL=public-read

# API Keys
# ========
NEWSAPI_KEY=your-newsapi-key
GUARDIAN_API_KEY=your-guardian-api-key
NYTIMES_API_KEY=your-nytimes-api-key

# Push Notifications
# =================
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_ADMIN_EMAIL=keshabkumarjha876@gmail.com

# Security
# ========
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# CORS
# ====
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Sentry (for error tracking)
# ===========================
SENTRY_DSN=your-sentry-dsn

# Google Analytics
# ===============
GOOGLE_ANALYTICS_ID=UA-XXXXXXXX-X
```

## 🛠 Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests with coverage report
coverage run manage.py test
coverage report -m
```

### Code Quality

This project enforces code quality using several tools:

- **Code Formatting**:
  ```bash
  black .
  isort .
  ```

- **Linting**:
  ```bash
  flake8
  mypy .
  ```

- **Security Checks**:
  ```bash
  bandit -r .
  safety check
  ```

### Pre-commit Hooks

Install pre-commit hooks to automatically run checks before each commit:

```bash
pre-commit install
```

### API Documentation

API documentation is available at `/api/docs/` when running the development server.

### Frontend Development

```bash
cd frontend
npm run dev  # Start development server
npm run build  # Build for production
```

## 🚀 Deployment

### Docker (Recommended)

1. **Build and start production containers**:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

2. **Run migrations**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

4. **Collect static files**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

### Manual Deployment

1. **Server Requirements**:
   - Linux server (Ubuntu 20.04+ recommended)
   - Python 3.9+
   - PostgreSQL 13+
   - Redis 6+
   - Nginx
   - Node.js 16+ & npm 8+

2. **Setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App.git
   cd NewsHub-Real-Time-News-Aggregator-Web-App
   
   # Set up Python environment
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements/production.txt
   
   # Configure environment variables
   cp .env.example .env
   nano .env  # Edit with your production settings
   
   # Set up database
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   
   # Set up Gunicorn
   pip install gunicorn
   cp config/gunicorn.service /etc/systemd/system/gunicorn.service
   systemctl start gunicorn
   systemctl enable gunicorn
   
   # Set up Nginx
   sudo cp config/nginx/newshub.conf /etc/nginx/sites-available/newshub
   sudo ln -s /etc/nginx/sites-available/newshub /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   
   # Set up Celery
   cp config/celery.service /etc/systemd/system/celery.service
   cp config/celery-beat.service /etc/systemd/system/celery-beat.service
   systemctl start celery
   systemctl enable celery
   systemctl start celery-beat
   systemctl enable celery-beat
   ```

### CI/CD

This project includes GitHub Actions workflows for:
- **CI Pipeline**: Runs tests, linting, and security checks on every push
- **CD Pipeline**: Automatically deploys to production when changes are pushed to the `main` branch

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by [Keshab Kumar](https://github.com/Keshabkjha)
- Django for the amazing web framework
- All the open-source libraries used in this project
- The developer community for their continuous support

## 📬 Contact

- **Name:** Keshab Kumar
- **Email:** [keshabkumarjha876@gmail.com](mailto:keshabkumarjha876@gmail.com)
- **GitHub:** [@Keshabkjha](https://github.com/Keshabkjha)
- **LinkedIn:** [Keshab Kumar](https://www.linkedin.com/in/keshabkjha/)
- **Twitter:** [@Keshabkjha](https://x.com/Keshabkjha)

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

Keshab Kumar - [@keshabkjha](https://twitter.com/keshabkjha) - keshabkumarjha876@gmail.com

Project Link: [https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App)

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework used
- [Django REST Framework](https://www.django-rest-framework.org/) - For building Web APIs
- [Tailwind CSS](https://tailwindcss.com/) - For styling
- [Celery](https://docs.celeryproject.org/) - For asynchronous task queue
- [PostgreSQL](https://www.postgresql.org/) - The database used
- [Redis](https://redis.io/) - For caching and message brokering
- [Docker](https://www.docker.com/) - For containerization

## ⭐ Show your support

Give a ⭐️ if this project helped you!

## 📜 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of all changes.

## 🔒 Security

Please review our [Security Policy](SECURITY.md) for reporting vulnerabilities.
