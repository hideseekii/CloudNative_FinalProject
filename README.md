# Cloud-Native-NYCU-Final_Project

## Project Overview

Cloud-Native-NYCU-FinalProject is a Django-based backend service for a restaurant ordering system. It demonstrates a cloud-native architecture with containerization, a RESTful API, and PostgreSQL for persistent storage.

## Features

* **User Management**: Registration, login, and profile editing (via `users/` app).
* **Menu Management**: CRUD operations for dishes, including support for images and descriptions (`menu/` app).
* **Order Processing**: Create and track customer orders (`orders/` app).
* **Dish Reviews**: Customers can leave reviews and ratings for dishes (`reviews/` app).
* **Admin Interface**: Manage all models through Django Admin.

## Repository Structure

```
Cloud-Native-NYCU-FinalProject/
├── CloudNative_final/    # Django project settings, wsgi, URLs
├── menu/                 # Menu app (models, views, templates)
├── orders/               # Orders app
├── reviews/              # Reviews app
├── users/                # User profile & auth extensions
├── static/               # Global static assets
├── templates/            # Base templates
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── .env.example          # Example environment variables
└── README.md
```

## Prerequisites

* Python 3.10+ or 3.12
* pip
* Docker & Docker Compose (optional, for containerized setup)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/AlHIO/Cloud-Native-NYCU-FinalProject.git
cd Cloud-Native-NYCU-FinalProject
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in values:

```
DB_NAME=project_db
DB_USER=AlHIO
DB_PASSWORD=postgre
DB_HOST=localhost      # or 'db' when using Docker
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=True
```

### 3. Local development (without Docker)

#### a. Create a virtual environment

```bash
python -m venv .venv
# PowerShell:
.\.venv\Scripts\Activate.ps1
# cmd.exe:
.venv\Scripts\activate.bat
# Bash:
source .venv/Scripts/activate
```

#### b. Install dependencies

```bash
pip install -r requirements.txt
```

#### c. Run database migrations

```bash
python manage.py migrate
```

#### d. Create a superuser

```bash
python manage.py createsuperuser
```

#### e. Start the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser; admin at `http://127.0.0.1:8000/admin/`.

### 4. Containerized setup (Docker)

Ensure Docker & Docker Compose are installed.

```bash
# Build and start services
docker-compose up --build -d

# Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

Access the app at `http://localhost:8000/`.

## API Endpoints

| Path              | Methods          | Description                   |
| ----------------- | ---------------- | ----------------------------- |
| `/api/auth/`      | POST, GET        | Login, logout, register       |
| `/api/menu/`      | GET, POST        | List & create dishes          |
| `/api/menu/<id>/` | GET, PUT, DELETE | Retrieve, update, delete dish |
| `/api/orders/`    | GET, POST        | List & create orders          |
| `/api/reviews/`   | GET, POST        | List & create reviews         |

*(Enable DRF browsable API or Swagger if configured.)*

## Running Tests

```bash
python manage.py test
```

## Contributing

1. Fork this repository
2. Create a branch: `git checkout -b feature/YourFeature`
3. Commit changes: `git commit -m "Add feature"`
4. Push: `git push origin feature/YourFeature`
5. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

*Happy coding!*
