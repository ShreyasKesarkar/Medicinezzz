# Medicinezzz System Setup & Run Guide

Medicinezzz is a complete, full-stack medication tracking application built with a **FastAPI backend** and a **Flutter frontend**, using a **Supabase (PostgreSQL)** database.

---

## 1. System Architecture Summary

```
Flutter (Web/Mobile) ──[HTTP REST]──> FastAPI Backend ──[Pooler Port 6543]──> Supabase (Postgres)
```

*   **FastAPI Backend**: Serves as the domain logic controller. Handles timezone-aware recurrence scheduling, event clustering, notification generation, and audit logging. Connects to Supabase using `asyncpg` with a connection pool configured for pgBouncer (statement cache size = 0).
*   **Flutter Frontend**: Provides a premium, dark-themed dashboard mapping the clustered timeline, medication wizard (Daily, Weekly, Every N Days), history log inspector, and local notifications. Uses Riverpod for state management and Dio for network requests.
*   **Supabase (Postgres)**: Hosts the database tables. Includes triggers enforcing the append-only nature of medical schedule versions, history audit trails, and note/instruction logs.

---

## 2. Backend Setup & Run

### Prerequisites
*   Python 3.10+
*   Pip

### Installation
1.  Navigate to the `backend/` directory:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install fastapi uvicorn asyncpg pydantic pydantic-settings httpx
    ```
3.  Configure your environment variables by creating a `.env` file matching [backend/.env.example](file:///c:/Users/Shreyas/Documents/Project/Medicinezzz/backend/.env.example):
    ```env
    DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xddmwrkjcxtffrnvwevq.supabase.co:6543/postgres?sslmode=require
    SUPABASE_URL=https://xddmwrkjcxtffrnvwevq.supabase.co
    SUPABASE_ANON_KEY=sb_publishable_Kljlpz8q5_CxKxAcnewqgQ_bcimKf5D
    ```

### Running the Backend
Start the Uvicorn development server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The interactive Swagger API documentation will be available at `http://localhost:8000/docs`.

### Running Automated Tests
Run the comprehensive test flow script (which validates registration, autoprovisioning, recurrence calculations, dose execution, corrections, pausing, and history logs):
```bash
python -m tests.test_flow
```

---

## 3. Frontend Setup & Run

### Prerequisites
*   Flutter SDK (3.22.0+ recommended)
*   Google Chrome (for Web targets) or Android Emulator/Device

### Installation
1.  Navigate to the `frontend/` directory:
    ```bash
    cd frontend
    ```
2.  Install packages:
    ```bash
    flutter pub get
    ```

### Running the App
*   **Run on Chrome**:
    ```bash
    flutter run -d chrome
    ```
*   **Run on Android**:
    ```bash
    flutter run -d android
    ```

### Building for Web Production
To compile a optimized, tree-shaken release build for deployment:
```bash
flutter build web
```
The output files will be created in the `build/web` directory.

---

## 4. Key Architectural Patterns

1.  **pgBouncer Transaction Pooling Compliance**: `asyncpg` pools are instantiated with `statement_cache_size=0`. This is required to prevent prepare statement cache mismatch errors on Supabase transaction-based pooling (Port 6543).
2.  **Concurrency / Double-Tap Prevention**: Changing dose status to `TAKEN` performs a transactional check to verify the current status is `PENDING`. If the database row has already changed status (indicating another user or thread modified it), it raises a `409 Conflict` and prevents double actions.
3.  **Append-Only Schema Trigger Integrity**: Triggers in the database prevent deletes and modifications on `medicine_schedule_versions` and `medicine_history`. Schedule state transitions are managed by adding time-bound pause/resume/finish instructions.
