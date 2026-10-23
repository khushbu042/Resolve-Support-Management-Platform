# Resolve Support Management Platform

A backend-focused support management platform built with **FastAPI, PostgreSQL, Redis, RabbitMQ, and AWS S3**. The application provides secure authentication, role-based ticket management, asynchronous email notifications, and cloud-based attachment storage.

This project focuses on practical backend engineering concepts, including REST API development, database migrations, caching, message queues, containerization, automated testing, CI/CD, and cloud deployment.

## Key Features

- **JWT Authentication:** Secure user registration and login with hashed passwords.
- **Role-Based Access Control (RBAC):** Separate permissions for customers, agents, and administrators.
- **Ticket Management:** Create, retrieve, update, assign, and manage support tickets.
- **Redis Rate Limiting:** Limit repeated failed login attempts to help protect authentication endpoints.
- **Asynchronous Notifications:** Use RabbitMQ to process ticket-related email notifications through a separate worker.
- **AWS S3 Integration:** Store ticket attachments in cloud object storage and generate presigned URLs for access.
- **PostgreSQL Database:** Persist application data using SQLAlchemy and manage schema changes with Alembic.
- **Docker Compose:** Run the application and its supporting services in containers.
- **Structured Logging:** Use Structlog to support application debugging and observability.
- **CI/CD:** Automate development checks and support the deployment workflow.

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend Framework | FastAPI |
| API Design | REST APIs |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Authentication | JWT, Password hashing |
| Caching and Rate Limiting | Redis |
| Message Broker | RabbitMQ |
| Asynchronous Messaging | aio-pika |
| File Storage | AWS S3, Boto3 |
| Email Testing | MailHog |
| Dependency Management | uv, `pyproject.toml`, `uv.lock` |
| Code Quality | Black, isort |
| Testing | pytest |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Deployment | AWS EC2 |

## Architecture

The application separates HTTP request handling from background notification processing.

```text
                    Client
                      |
                      v
               FastAPI Application
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
      PostgreSQL    Redis       AWS S3
      (Data)      (Rate Limit)  (Files)
          |
          v
      Ticket Workflow
          |
          v
       RabbitMQ
          |
          v
   Notification Worker
          |
          v
      Email Service
       (MailHog)
```

### How It Works

1. A user registers and authenticates using the API.
2. JWT authentication and role-based authorization protect restricted endpoints.
3. Customers create support tickets, which are stored in PostgreSQL.
4. Redis helps enforce login rate limits.
5. Ticket-related notification events are published to RabbitMQ.
6. A separate notification worker consumes messages and processes email notifications.
7. Ticket attachments are stored in AWS S3, while the application manages their associated metadata.
8. Docker Compose coordinates the application and its supporting services.

## User Roles

| Role | Responsibilities |
|---|---|
| Customer | Register, log in, create tickets, view tickets, and upload attachments. |
| Agent | Access authorized ticket operations and work on assigned tickets. |
| Admin | Manage ticket assignments and perform administrative operations. |

Access to protected resources depends on the authenticated user's role and the application's authorization rules.

## API Endpoints

The following are the main API routes. Refer to the interactive API documentation for the available request schemas and response details.

### Health Checks

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Check application health |
| GET | `/api/v1/health/ready` | Check application readiness |

### Authentication and Users

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/users/register` | Register a user |
| POST | `/api/v1/users/login` | Authenticate a user |

### Ticket Management

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/tickets/tickets` | Create a ticket |
| GET | `/api/v1/tickets/tickets` | Retrieve tickets accessible to the user |
| PATCH | `/api/v1/tickets/{ticket_id}` | Update a ticket |
| DELETE | `/api/v1/tickets/{ticket_id}` | Delete a ticket |
| POST | `/api/v1/tickets/{ticket_id}/assign` | Assign a ticket to an agent |
| POST | `/api/v1/tickets/{ticket_id}/attachments` | Upload a ticket attachment |

**Note:** Request bodies, query parameters, response schemas, and access permissions depend on the individual endpoint implementation.

## Project Structure

```text
Resolve-Support-Management-Platform/
├── .github/
│   └── workflows/          # CI/CD workflow configuration
├── alembic/                 # Database migration scripts
├── api/
│   └── openapi/             # API-related specifications
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/             # API route modules
│   ├── services/            # Application and integration services
│   └── workers/             # Background notification processing
├── tests/
│   └── unit/                # Unit tests
├── .dockerignore
├── .env.example              # Environment variable template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml            # Project and dependency configuration
├── uv.lock                   # Locked dependency versions
└── README.md
```

The exact contents of individual application directories may evolve as the project develops.

## Prerequisites

Before running the project locally, install:

- Python 3.11 or a compatible version supported by the project.
- Docker and Docker Compose.
- uv, the Python package and project manager.
- AWS credentials and an S3 bucket if you want to test attachment storage.

You can install uv by following the official [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/khushbu042/Resolve-Support-Management-Platform.git

cd Resolve-Support-Management-Platform
```

### 2. Configure Environment Variables

Create your local environment file from the example:

```bash
cp .env.example .env
```

Update `.env` with the configuration required by your application.

Typical settings include:

```dotenv
# Database
DATABASE_URL=your_database_connection_string
POSTGRES_USER=your_database_user
POSTGRES_PASSWORD=your_database_password
POSTGRES_DB=your_database_name

# Authentication
JWT_SECRET_KEY=your_secret_key

# Redis
REDIS_URL=redis://redis:6379

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# AWS S3
AWS_REGION=your_aws_region
AWS_S3_BUCKET=your_bucket_name
```

These are illustrative settings. Use the exact variable names expected by your application and `.env.example`. Configure the remaining SMTP and application settings required by your implementation.

**Security:** Never commit your actual `.env` file, AWS credentials, database passwords, or JWT secrets to GitHub. For AWS deployment, prefer an IAM role attached to the EC2 instance instead of long-lived access keys.

### 3. Start the Application with Docker Compose

Build the application image:

```bash
docker compose build
```

Start the application and supporting services:

```bash
docker compose up -d
```

Check the running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f app
```

View the notification worker logs:

```bash
docker compose logs -f notification-worker
```

The Docker Compose configuration includes the FastAPI application, PostgreSQL, Redis, RabbitMQ, MailHog, and the notification worker.

### 4. Apply Database Migrations

Once the containers are running, apply the Alembic migrations:

```bash
docker compose exec app uv run alembic upgrade head
```

This brings the database schema up to the latest migration revision.

### 5. Access the Application

| Resource | Address |
|---|---|
| FastAPI API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| RabbitMQ Management UI | http://localhost:15672 |
| MailHog Email UI | http://localhost:8025 |

The application API is available at port `8000`. MailHog provides a local interface for inspecting test emails generated by the notification workflow.

The RabbitMQ management interface uses the credentials configured for the RabbitMQ service.

## Running Locally Without Docker

You can also run the FastAPI application directly on your machine.

### 1. Install Dependencies

```bash
uv sync --locked
```

### 2. Configure the Environment

Create and update your `.env` file. Ensure PostgreSQL, Redis, and RabbitMQ are accessible at the addresses specified in your configuration.

If these services are running through Docker Compose, remember that container hostnames such as `db` and `redis` normally resolve inside the Docker network. When running FastAPI directly on your host machine, configure the corresponding service addresses using their exposed host ports.

### 3. Run Database Migrations

```bash
uv run alembic upgrade head
```

### 4. Start FastAPI

```bash
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to explore the API.

**Note:** Running FastAPI directly does not automatically start the separate notification worker. Start that worker separately if you want to test asynchronous email processing.

## Testing and Code Quality

The project uses pytest for automated testing and Black and isort for formatting and import organization.

Run the tests:

```bash
uv run pytest
```

Check code formatting:

```bash
uv run black --check .
```

Check import organization:

```bash
uv run isort --check-only .
```

Automatically format code:

```bash
uv run black .
uv run isort .
```

Run these checks locally before pushing changes. The GitHub Actions workflow can then run the configured checks automatically when the relevant workflow triggers occur.

## CI/CD

The project uses GitHub Actions to automate development checks and support continuous delivery.

### Continuous Integration (CI)

The CI workflow can validate:

- Python code formatting with Black.
- Import organization with isort.
- Automated tests with pytest.

These checks help identify formatting problems and regressions before changes are merged or deployed.

### Continuous Deployment (CD)

The deployment workflow supports delivering application changes to the deployment environment.

The application is containerized with Docker and deployed on AWS EC2.

The deployment process should use securely configured environment variables, verify the application starts successfully, and run database migrations when required.

See the workflow definitions under `.github/workflows/` for the actual triggers, jobs, and deployment steps configured in this repository.

## Deployment

The application has been deployed to AWS EC2 using Docker-based deployment.

The deployment setup provides practical experience with:

- Provisioning a cloud virtual machine.
- Running containerized application services.
- Configuring environment variables and service connectivity.
- Managing database migrations.
- Exposing the application through the appropriate network configuration.
- Automating deployment steps through CI/CD.

For a production deployment, configure HTTPS, restrict inbound network access, secure credentials, and use persistent storage and appropriate backup policies.

## Engineering Concepts Demonstrated

This project provides hands-on practice with:

- REST API design and request validation.
- JWT authentication and role-based authorization.
- Relational database design and schema migrations.
- Password hashing and login rate limiting.
- Asynchronous event-driven processing with RabbitMQ.
- Background workers and email notifications.
- Object storage and presigned URLs with AWS S3.
- Container networking and service orchestration.
- Automated testing and code quality checks.
- CI/CD and cloud deployment.
- Structured application logging and health checks.

## Future Improvements

Potential improvements as the project evolves include:

- Expanding unit and integration test coverage.
- Adding stronger monitoring and operational metrics.
- Improving notification reliability with retry policies and dead-letter queues.
- Introducing more robust event delivery and idempotent processing.
- Enhancing deployment safety and rollback procedures.
- Adding broader end-to-end testing.

These are potential enhancements, not claims about currently implemented functionality.

## Learning Objectives

Resolve Support Management Platform is a hands-on backend engineering project built to understand how application components work together beyond basic CRUD APIs.

The focus is on writing maintainable APIs, managing state and permissions, integrating infrastructure services, handling asynchronous operations, and deploying a containerized application to the cloud.

## Author

**Khushbu Mourya**

- GitHub: [@khushbu042](https://github.com/khushbu042)
- Repository: [Resolve Support Management Platform](https://github.com/khushbu042/Resolve-Support-Management-Platform)
