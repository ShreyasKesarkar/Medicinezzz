# Medicinezzz

Medicinezzz is a premium, full-stack medication tracking application built with a **FastAPI backend** and a **Flutter frontend**, using a **Supabase (PostgreSQL)** database.

It is designed for patients to log and coordinate their medication schedules, notes, instructions, and history logs in a high-contrast, premium interface.

## 🔑 Core Features

1.  **Timezone-Aware Clustered Timeline**: Groups individual medicines scheduled for the exact same hour into a single, unified action card.
2.  **Flexible Wizard Recurrences**: Supports Daily, Weekly (selected day), and Every N Days recurrence intervals.
3.  **Strict Transaction Controls**: Protects against double-actions and double-taps on dose marking.
4.  **Complete Audit Logs**: Preserves every single medication state change, dose action, correction, note, and instruction, complying with append-only database triggers.
5.  **Local Push Reminders**: Notifies patients of pending scheduled event clusters.
6.  **Premium Medical Interface**: Dark-themed, highly readable layout with Outfitter/Inter typography and status colors.

## 🚀 Quick Start

For detailed setup, installation, environment configuration, and execution instructions, please refer to the [Setup Guide](file:///c:/Users/Shreyas/Documents/Project/Medicinezzz/docs/setup.md).

### Run Backend
```bash
cd backend
pip install -r requirements.txt # (or install packages)
uvicorn app.main:app --reload
```

### Run Frontend
```bash
cd frontend
flutter pub get
flutter run -d chrome
```

### Run Tests
```bash
cd backend
python -m tests.test_flow
```
