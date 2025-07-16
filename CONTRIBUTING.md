# Contributing to NewsHub

Thank you for considering contributing to NewsHub! We welcome all contributions, whether it's bug reports, feature requests, documentation improvements, or code contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Style Guides](#style-guides)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Style Guide](#python-style-guide)
  - [JavaScript Style Guide](#javascript-style-guide)
  - [Documentation Style Guide](#documentation-style-guide)
- [Code Review Process](#code-review-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Bugs are tracked as [GitHub issues](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/issues). Before creating a new issue:

1. **Check if the issue has already been reported** by searching under [Issues](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/issues).
2. If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/issues/new/choose). Be sure to include:
   - A clear and descriptive title
   - A description of the expected behavior and the observed behavior
   - Steps to reproduce the issue
   - Any relevant screenshots or error messages
   - Your environment (OS, browser, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Before creating an enhancement suggestion:

1. Check if a similar enhancement has already been suggested.
2. Provide a clear and descriptive title and description of the enhancement.
3. Explain why this enhancement would be useful to most NewsHub users.
4. Include any relevant screenshots or mockups if applicable.

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through the `good first issue` and `help wanted` issues:
- [Good first issues](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/labels/good%20first%20issue) - issues which should only require a few lines of code, and a test or two.
- [Help wanted](https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App/labels/help%20wanted) - issues which should be a bit more involved than `beginner` issues.

### Pull Requests

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Node.js & npm
- Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Keshabkjha/NewsHub-Real-Time-News-Aggregator-Web-App.git
   cd NewsHub-Real-Time-News-Aggregator-Web-App
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
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

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

### Using Docker

1. **Build and start the containers**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

The application will be available at http://localhost:8000

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line
- When only changing documentation, include `[ci skip]` in the commit title

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for code formatting
- Use [isort](https://github.com/timothycrosley/isort) for import sorting
- Use [flake8](https://flake8.pycqa.org/) for linting

### JavaScript Style Guide

- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use [Prettier](https://prettier.io/) for code formatting
- Use [ESLint](https://eslint.org/) for linting

### Documentation Style Guide

- Use [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep documentation up-to-date with code changes
- Add docstrings to all public modules, functions, classes, and methods

## Code Review Process

1. A maintainer will review your pull request and provide feedback.
2. Once all feedback has been addressed, your pull request will be merged.
3. The `main` branch is automatically deployed to production after passing all tests.

## Community

- Join our [Discord server](https://discord.gg/your-discord-invite) to chat with the community
- Follow us on [Twitter](https://twitter.com/your-twitter-handle) for updates

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
