import asyncpg
from uuid import UUID
from typing import Optional

class PatientRepository:
    @staticmethod
    async def get_patient_by_id(conn: asyncpg.Connection, patient_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT p.id as patient_id, u.id as user_id, u.full_name, u.timezone, p.date_of_birth
            FROM patients p
            JOIN user_profiles u ON p.user_id = u.id
            WHERE p.id = $1::uuid;
        """, patient_id)
        return dict(row) if row else None

    @staticmethod
    async def get_patient_by_user_id(conn: asyncpg.Connection, user_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT p.id as patient_id, u.id as user_id, u.full_name, u.timezone, p.date_of_birth
            FROM patients p
            JOIN user_profiles u ON p.user_id = u.id
            WHERE u.id = $1::uuid;
        """, user_id)
        return dict(row) if row else None
