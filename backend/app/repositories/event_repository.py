import asyncpg
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class EventRepository:
    @staticmethod
    async def get_event_by_time(conn: asyncpg.Connection, patient_id: UUID, scheduled_at: datetime) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT * FROM medication_events
            WHERE patient_id = $1::uuid AND scheduled_at = $2;
        """, patient_id, scheduled_at)
        return dict(row) if row else None

    @staticmethod
    async def create_event(conn: asyncpg.Connection, patient_id: UUID, scheduled_at: datetime) -> UUID:
        e_id = await conn.fetchval("""
            INSERT INTO medication_events (patient_id, scheduled_at)
            VALUES ($1::uuid, $2)
            RETURNING id;
        """, patient_id, scheduled_at)
        return e_id

    @staticmethod
    async def get_event_dose_by_schedule_and_event(
        conn: asyncpg.Connection,
        schedule_id: UUID,
        event_id: UUID
    ) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT * FROM event_doses
            WHERE schedule_id = $1::uuid AND event_id = $2::uuid;
        """, schedule_id, event_id)
        return dict(row) if row else None

    @staticmethod
    async def get_event_dose_by_id(conn: asyncpg.Connection, dose_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT d.*, m.name as medicine_name, u.name as dosage_unit_name
            FROM event_doses d
            JOIN medicines m ON d.medicine_id = m.id
            JOIN dosage_units u ON d.dosage_unit_id = u.id
            WHERE d.id = $1::uuid;
        """, dose_id)
        return dict(row) if row else None

    @staticmethod
    async def create_event_dose(
        conn: asyncpg.Connection,
        event_id: UUID,
        medicine_id: UUID,
        schedule_id: UUID,
        schedule_version_id: UUID,
        dosage_amount: float,
        dosage_unit_id: UUID,
        scheduled_at: datetime,
        status: str = "PENDING"
    ) -> UUID:
        d_id = await conn.fetchval("""
            INSERT INTO event_doses (
                event_id, medicine_id, schedule_id, schedule_version_id,
                dosage_amount, dosage_unit_id, scheduled_at, status
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6::uuid, $7, $8)
            RETURNING id;
        """, event_id, medicine_id, schedule_id, schedule_version_id,
           dosage_amount, dosage_unit_id, scheduled_at, status)
        return d_id

    @staticmethod
    async def update_dose_status(
        conn: asyncpg.Connection,
        dose_id: UUID,
        status: str,
        actual_taken_at: Optional[datetime],
        status_changed_at: datetime,
        status_remark: Optional[str],
        expected_status: Optional[str] = None
    ) -> bool:
        # Atomic update with conditional statement (concurrency protection)
        query = """
            UPDATE event_doses
            SET status = $2, 
                actual_taken_at = $3, 
                status_changed_at = $4, 
                status_remark = $5
            WHERE id = $1::uuid
        """
        params = [dose_id, status, actual_taken_at, status_changed_at, status_remark]
        
        if expected_status:
            params.append(expected_status)
            query += f" AND status = ${len(params)}"
            
        result = await conn.execute(query, *params)
        # result is like "UPDATE 1" or "UPDATE 0"
        return result == "UPDATE 1"

    @staticmethod
    async def get_doses_for_patient(
        conn: asyncpg.Connection,
        patient_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        # Fetches all doses in range along with medicine details in a single query
        rows = await conn.fetch("""
            SELECT d.id as dose_id, d.event_id, d.medicine_id, d.schedule_id, d.schedule_version_id,
                   d.dosage_amount, d.scheduled_at, d.status, d.actual_taken_at, d.status_changed_at, d.status_remark,
                   m.name as medicine_name, t.name as medicine_type_name, u.name as dosage_unit_name
            FROM event_doses d
            JOIN medication_events e ON d.event_id = e.id
            JOIN medicines m ON d.medicine_id = m.id
            LEFT JOIN medicine_types t ON m.medicine_type_id = t.id
            JOIN dosage_units u ON d.dosage_unit_id = u.id
            WHERE e.patient_id = $1::uuid AND d.scheduled_at >= $2 AND d.scheduled_at <= $3
            ORDER BY d.scheduled_at ASC, m.name ASC;
        """, patient_id, start_time, end_time)
        return [dict(r) for r in rows]

    @staticmethod
    async def create_notification(conn: asyncpg.Connection, event_id: UUID, scheduled_for: datetime) -> UUID:
        n_id = await conn.fetchval("""
            INSERT INTO event_notifications (event_id, scheduled_for)
            VALUES ($1::uuid, $2)
            ON CONFLICT (event_id) DO UPDATE SET scheduled_for = EXCLUDED.scheduled_for
            RETURNING id;
        """, event_id, scheduled_for)
        return n_id

    @staticmethod
    async def get_notification_by_event(conn: asyncpg.Connection, event_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT * FROM event_notifications WHERE event_id = $1::uuid;
        """, event_id)
        return dict(row) if row else None

    @staticmethod
    async def delete_notification(conn: asyncpg.Connection, event_id: UUID) -> None:
        await conn.execute("""
            DELETE FROM event_notifications WHERE event_id = $1::uuid;
        """, event_id)
