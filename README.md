# Foccai - Basic ECD System

A web application for managing patient Electronic Clinical Documents (ECDs). This system allows medical data collectors to record patient information and upload documents, while auditors can review and classify the clinical records.

## Features

- **Role-Based Access Control**:
  - **Collector**: Create patient profiles, upload medical records, and submit ECDs for audit.
  - **Auditor**: Review submitted ECDs and classify them (ECD1, ECD2, ECD3).
- **Secure Document Storage**: Upload and manage medical records securely.
- **Dockerized Environment**: easy setup with Docker and Docker Compose.
- **Environment Security**: Sensitive credentials managed via `.env` files.

## Tech Stack

- **Backend**: Python, Flask
- **Database**: MongoDB
- **Frontend**: HTML5, CSS3 (Vanilla), Jinja2
- **Containerization**: Docker, Docker Compose

## Project Structure

```text
.
├── backend/            # Flask application and DB logic
│   ├── app.py          # Main application routes
│   ├── db.py           # Database connection & initialization
│   └── requirements.txt
├── frontend/           # UI components
│   ├── static/         # CSS and uploaded files
│   └── templates/      # HTML Jinja2 templates
├── .env                # Environment variables (Ignored by Git)
├── Dockerfile          # Web service container configuration
└── docker-compose.yaml # Orchestration for Web & MongoDB
```

## Setup & Installation

### Option 1: Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone git@github.com:sherin23/basic-ECD-app.git
   cd basic-ECD-app
   ```

2. **Configure environment variables**:
   Create a `.env` file in the root directory (based on the project requirements):
   ```text
   MONGO_INITDB_ROOT_USERNAME=admin
   MONGO_INITDB_ROOT_PASSWORD=admin@123
   FLASK_SECRET_KEY=your_secret_key
   MONGO_URI=mongodb://admin:admin%40123@mongo:27017/patient_ecd_db?authSource=admin
   ```

3. **Run with Docker Compose**:
   ```bash
   docker compose up --build
   ```

4. **Access the app**:
   Open [http://localhost:5000](http://localhost:5000) in your browser.

### Option 2: Local Development

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Setup MongoDB**:
   Ensure you have a MongoDB instance running and update the `MONGO_URI` in your `.env` file to point to it (e.g., `localhost:27017`).

4. **Run the application**:
   ```bash
   python backend/app.py
   ```

## Default Credentials

The database is automatically seeded with these test accounts:

| Role      | Username    | Password |
|-----------|-------------|----------|
| Collector | `collector` | `password` |
| Auditor   | `auditor`   | `password` |

## Security Note

The `.env` file contains sensitive information and is excluded from version control via `.gitignore`. Never commit your real credentials to public repositories.
