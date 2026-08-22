import asyncpg
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class MedicineRepository:
    @staticmethod
    async def get_medicines(conn: asyncpg.Connection, patient_id: UUID, status: Optional[str] = None) -> List[dict]:
        query = """
            SELECT m.*, t.name as medicine_type_name
            FROM medicines m
            LEFT JOIN medicine_types t ON m.medicine_type_id = t.id
            WHERE m.patient_id = $1::uuid
        """
        params = [patient_id]
        if status:
            query += " AND m.status = $2"
            params.append(status)
        query += " ORDER BY m.name ASC;"
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]

    @staticmethod
    async def get_medicine_by_id(conn: asyncpg.Connection, medicine_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT m.*, t.name as medicine_type_name
            FROM medicines m
            LEFT JOIN medicine_types t ON m.medicine_type_id = t.id
            WHERE m.id = $1::uuid;
        """, medicine_id)
        return dict(row) if row else None

    @staticmethod
    async def create_medicine(
        conn: asyncpg.Connection,
        patient_id: UUID,
        name: str,
        medicine_type_id: Optional[UUID] = None,
        status: str = "ACTIVE"
    ) -> UUID:
        m_id = await conn.fetchval("""
            INSERT INTO medicines (patient_id, name, medicine_type_id, status)
            VALUES ($1::uuid, $2, $3::uuid, $4)
            RETURNING id;
        """, patient_id, name, medicine_type_id, status)
        return m_id

    @staticmethod
    async def update_medicine(
        conn: asyncpg.Connection,
        medicine_id: UUID,
        name: Optional[str] = None,
        medicine_type_id: Optional[UUID] = None,
        status: Optional[str] = None,
        finished_at: Optional[datetime] = None,
        stopped_at: Optional[datetime] = None
    ) -> None:
        updates = []
        params = []
        
        if name is not None:
            params.append(name)
            updates.append(f"name = ${len(params)}")
        if medicine_type_id is not None:
            params.append(medicine_type_id)
            updates.append(f"medicine_type_id = ${len(params)}")
        if status is not None:
            params.append(status)
            updates.append(f"status = ${len(params)}")
        if finished_at is not None:
            params.append(finished_at)
            updates.append(f"finished_at = ${len(params)}")
        if stopped_at is not None:
            params.append(stopped_at)
            updates.append(f"stopped_at = ${len(params)}")
            
        if not updates:
            return
            
        params.append(medicine_id)
        query = f"UPDATE medicines SET {', '.join(updates)}, updated_at = now() WHERE id = ${len(params)}::uuid;"
        await conn.execute(query, *params)

    @staticmethod
    async def get_or_create_type(conn: asyncpg.Connection, patient_id: UUID, name: str) -> UUID:
        # Search globally case-insensitively
        row = await conn.fetchrow("""
            SELECT id FROM medicine_types
            WHERE LOWER(name) = LOWER($1);
        """, name)
        if row:
            return row["id"]
            
        # Create user-defined type
        t_id = await conn.fetchval("""
            INSERT INTO medicine_types (name, is_system_defined, is_active, created_by)
            VALUES ($1, false, true, $2::uuid)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, name.capitalize(), patient_id)
        return t_id

    @staticmethod
    async def get_or_create_unit(conn: asyncpg.Connection, patient_id: UUID, name: str) -> UUID:
        # Search globally case-insensitively
        row = await conn.fetchrow("""
            SELECT id FROM dosage_units
            WHERE LOWER(name) = LOWER($1);
        """, name)
        if row:
            return row["id"]
            
        # Create user-defined unit
        u_id = await conn.fetchval("""
            INSERT INTO dosage_units (name, is_system_defined, is_active, created_by)
            VALUES ($1, false, true, $2::uuid)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """, name.lower(), patient_id)
        return u_id

    @staticmethod
    async def get_medicine_types(conn: asyncpg.Connection, patient_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT * FROM medicine_types
            ORDER BY is_system_defined DESC, name ASC;
        """)
        return [dict(r) for r in rows]

    @staticmethod
    async def get_dosage_units(conn: asyncpg.Connection, patient_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT * FROM dosage_units
            ORDER BY is_system_defined DESC, name ASC;
        """)
        return [dict(r) for r in rows]
