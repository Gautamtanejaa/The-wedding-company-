# Organization Management Service (Backend Assignment)

Backend implementation for the **Backend Intern Assignment - Organization Management Service**.

This project is a **backend-only** service built with **FastAPI** and **MongoDB** that manages organizations and their admin users in a multi-tenant style. It uses a **master database** for global metadata and creates **dynamic MongoDB collections per organization**.

## Tech Stack

- Python
- FastAPI
- MongoDB (via Motor, the async driver)
- JWT for authentication (python-jose)
- bcrypt password hashing (passlib)

## Project Structure

- `app/`
  - `main.py` – FastAPI application entrypoint
  - `config.py` – Environment-based configuration (MongoDB, JWT, etc.)
  - `db.py` – MongoDB connection helper (Motor)
  - `auth.py` – Password hashing, JWT creation/verification, auth dependencies
  - `schemas.py` – Pydantic models for request/response validation
  - `models.py` – Data access helpers and organization/admin operations
  - `routers/`
    - `org.py` – Organization CRUD endpoints
    - `admin.py` – Admin login endpoint

## Setup & Running Locally

### 1. Prerequisites

- Python 3.10+ recommended
- MongoDB running locally or in the cloud

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

The service reads configuration from environment variables (with sensible defaults):

- `MONGODB_URI` – default: `mongodb://localhost:27017`
- `MONGODB_DB_NAME` – default: `org_service`
- `JWT_SECRET_KEY` – default: `change_me_in_production` (change this in real usage)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` – default: `60`

On Windows PowerShell, you can set them like:

```powershell
$env:MONGODB_URI = "mongodb://localhost:27017"
$env:JWT_SECRET_KEY = "your_strong_secret_here"
```

### 4. Run the server

From the project root:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` and the automatic docs at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Overview

### 1. Create Organization

- **Endpoint**: `POST /org/create`
- **Auth**: None
- **Body (JSON)**:

```json
{
  "organization_name": "Acme Corp",
  "email": "admin@acme.com",
  "password": "strongpassword"
}
```

- **Behavior**:
  - Validates that the organization name (slug) does not already exist.
  - Creates an admin user with hashed password.
  - Stores organization metadata in the master `organizations` collection.
  - Stores admin in master `admins` collection, linked via `organization_id`.
  - Creates a dynamic collection named `org_<slugified_org_name>`.

### 2. Get Organization by Name

- **Endpoint**: `GET /org/get?organization_name=<name>`
- **Auth**: None
- **Behavior**:
  - Fetches organization metadata from the master `organizations` collection.
  - Returns 404 if not found.

### 3. Update Organization

- **Endpoint**: `PUT /org/update`
- **Auth**: Admin JWT required (`Authorization: Bearer <token>`)
- **Body (JSON)**:

```json
{
  "organization_name": "New Org Name (optional)",
  "email": "new-admin-email@example.com (optional)",
  "password": "newpassword (optional)"
}
```

- **Behavior**:
  - Uses the authenticated admin's organization as the target.
  - If `organization_name` is provided and different:
    - Validates that no other organization uses that name.
    - Computes a new slug and collection name `org_<new_slug>`.
    - Creates the new collection and copies data from the old collection.
    - Drops the old collection after successful migration.
    - Updates organization metadata in the master database.
  - If `email` or `password` are provided, updates the admin credentials (password is re-hashed).

> Note: The original assignment lists `organization_name`, `email`, and `password` as inputs for update. Here we interpret `organization_name` as the **new** name for the authenticated admin's organization and document this clearly.

### 4. Delete Organization

- **Endpoint**: `DELETE /org/delete`
- **Auth**: Admin JWT required
- **Body (JSON)**:

```json
{
  "organization_name": "Exact Org Name"
}
```

- **Behavior**:
  - Only allows deletion when:
    - The JWT belongs to the admin of this organization, and
    - The provided `organization_name` matches the stored organization name.
  - Deletes the org metadata from `organizations`.
  - Deletes the associated admin from `admins`.
  - Drops the dynamic collection for that organization.

### 5. Admin Login

- **Endpoint**: `POST /admin/login`
- **Auth**: None
- **Body (JSON)**:

```json
{
  "email": "admin@acme.com",
  "password": "strongpassword"
}
```

- **Behavior**:
  - Validates the admin's email and password (hashed with bcrypt).
  - On success, returns a JWT containing:
    - `sub`: admin ID
    - `org_id`: organization ID
    - `org_name`: organization name
  - On failure, returns 401.

## High-Level Architecture

**Master Database (single MongoDB database)**

- `organizations` collection:
  - name
  - slug
  - collection_name (e.g. `org_acme_corp`)
  - admin_id
  - created_at, updated_at
- `admins` collection:
  - email
  - password_hash
  - organization_id
  - created_at

**Dynamic Collections**

- For each organization with slug `acme_corp`, a collection `org_acme_corp` is created.
- Initially empty (you can later store org-specific entities like members, projects, etc.).

## Design Choices & Trade-offs

### Is this architecture scalable?

**Pros:**

- Clear separation of data per organization via `org_<slug>` collections.
- Easy to add more organization-specific collections or fields without impacting others.
- FastAPI + MongoDB (Motor) is lightweight and well-suited for I/O-bound workloads.
- JWT-based auth scales well horizontally (stateless).

**Trade-offs / Cons:**

- **Many collections**: With a large number of organizations, you end up with many Mongo collections, which can impact performance and management (indexes, migrations, backups).
- **Cross-tenant analytics**: Queries that span all organizations (e.g., global reporting) are harder compared to a single shared collection keyed by `organization_id`.
- **Operational complexity**: Managing indexes and performance per collection can be more work than a single multi-tenant collection.

### Alternative design

An alternative multi-tenant design is:

- Single `organizations` collection (as now).
- Single `admins` collection (as now).
- Single shared collection for tenant data (e.g. `records`), with a field `organization_id`.
- All org-specific queries filter by `organization_id` and are protected at the application level.

**Benefits of alternative:**

- Fewer collections (easier to manage, index, and back up).
- Global analytics and reporting become easier.

**Downside:**

- Logical separation only (within one collection), so bugs in the application layer can cause cross-tenant data leaks if access control is incorrect.

### Why this design is reasonable here

For an assignment and for small-to-medium scale:

- Using dynamic collections per organization matches the requirement explicitly.
- It demonstrates understanding of multi-tenant patterns and dynamic schema/collection management.
- The code is modular (separate routers, auth, models) and can be extended with more org-specific entities later.

## Notes

- This implementation focuses on backend functionality only, as requested.
- For production, you would add:
  - More robust error handling & logging.
  - Indexes on frequently queried fields (e.g. `organizations.slug`, `admins.email`).
  - Input rate-limiting and stronger security around JWT secrets and key rotation.

 ## Simple Diagram
<img width="732" height="759" alt="image" src="https://github.com/user-attachments/assets/d21a0ab4-7f98-4703-bbb8-8a6c8e58fbf7" />




