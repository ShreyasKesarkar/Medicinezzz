import asyncpg
from uuid import UUID
from datetime import datetime, date, time
from typing import List, Optional

class ScheduleRepository:
    @staticmethod
    async def create_schedule(conn: asyncpg.Connection, medicine_id: UUID, status: str = "ACTIVE") -> UUID:
        s_id = await conn.fetchval("""
            INSERT INTO medicine_schedules (medicine_id, status)
            VALUES ($1::uuid, $2)
            RETURNING id;
        """, medicine_id, status)
        return s_id

    @staticmethod
    async def create_schedule_version(
        conn: asyncpg.Connection,
        schedule_id: UUID,
        version_number: int,
        schedule_time: time,
        dosage_amount: float,
        dosage_unit_id: UUID,
        frequency: str,
        weekday: Optional[int],
        interval_days: Optional[int],
        start_date: date,
        planned_end_date: Optional[date],
        effective_from: datetime,
        effective_until: Optional[datetime] = None,
        change_remark: Optional[str] = None
    ) -> UUID:
        v_id = await conn.fetchval("""
            INSERT INTO medicine_schedule_versions (
                schedule_id, version_number, schedule_time, dosage_amount, dosage_unit_id,
                frequency, weekday, interval_days, start_date, planned_end_date,
                effective_from, effective_until, change_remark
            )
            VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id;
        """, schedule_id, version_number, schedule_time, dosage_amount, dosage_unit_id,
           frequency, weekday, interval_days, start_date, planned_end_date,
           effective_from, effective_until, change_remark)
        return v_id

    @staticmethod
    async def get_schedules_by_medicine_id(conn: asyncpg.Connection, medicine_id: UUID) -> List[dict]:
        # Uses LEFT JOIN LATERAL to get the latest schedule version
        rows = await conn.fetch("""
            SELECT s.*, 
                   v.id as version_id, v.version_number, v.schedule_time, v.dosage_amount, v.dosage_unit_id,
                   v.frequency, v.weekday, v.interval_days, v.start_date, v.planned_end_date,
                   v.effective_from, v.effective_until, v.change_remark,
                   u.name as dosage_unit_name
            FROM medicine_schedules s
            LEFT JOIN LATERAL (
                SELECT * FROM medicine_schedule_versions 
                WHERE schedule_id = s.id
                ORDER BY version_number DESC LIMIT 1
            ) v ON TRUE
            LEFT JOIN dosage_units u ON v.dosage_unit_id = u.id
            WHERE s.medicine_id = $1::uuid;
        """, medicine_id)
        return [dict(r) for r in rows]

    @staticmethod
    async def get_schedule_by_id(conn: asyncpg.Connection, schedule_id: UUID) -> Optional[dict]:
        row = await conn.fetchrow("""
            SELECT s.*, 
                   v.id as version_id, v.version_number, v.schedule_time, v.dosage_amount, v.dosage_unit_id,
                   v.frequency, v.weekday, v.interval_days, v.start_date, v.planned_end_date,
                   v.effective_from, v.effective_until, v.change_remark,
                   u.name as dosage_unit_name,
                   m.name as medicine_name
            FROM medicine_schedules s
            LEFT JOIN LATERAL (
                SELECT * FROM medicine_schedule_versions 
                WHERE schedule_id = s.id
                ORDER BY version_number DESC LIMIT 1
            ) v ON TRUE
            LEFT JOIN dosage_units u ON v.dosage_unit_id = u.id
            LEFT JOIN medicines m ON s.medicine_id = m.id
            WHERE s.id = $1::uuid;
        """, schedule_id)
        return dict(row) if row else None

    @staticmethod
    async def get_schedule_versions(conn: asyncpg.Connection, schedule_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT v.*, u.name as dosage_unit_name
            FROM medicine_schedule_versions v
            LEFT JOIN dosage_units u ON v.dosage_unit_id = u.id
            WHERE v.schedule_id = $1::uuid
            ORDER BY v.version_number DESC;
        """, schedule_id)
        return [dict(r) for r in rows]

    @staticmethod
    async def get_schedule_version_at_time(
        conn: asyncpg.Connection,
        schedule_id: UUID,
        check_time: datetime
    ) -> Optional[dict]:
        # Finds the version that was active at the specific check_time (the latest version where effective_from <= check_time)
        row = await conn.fetchrow("""
            SELECT v.*, u.name as dosage_unit_name
            FROM medicine_schedule_versions v
            LEFT JOIN dosage_units u ON v.dosage_unit_id = u.id
            WHERE v.schedule_id = $1::uuid
              AND v.effective_from <= $2
            ORDER BY v.version_number DESC
            LIMIT 1;
        """, schedule_id, check_time)
        return dict(row) if row else None

    @staticmethod
    async def get_active_schedules_for_patient(conn: asyncpg.Connection, patient_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT s.id as schedule_id, s.medicine_id,
                   v.id as version_id, v.version_number, v.schedule_time, v.dosage_amount, v.dosage_unit_id,
                   v.frequency, v.weekday, v.interval_days, v.start_date, v.planned_end_date,
                   v.effective_from, v.effective_until,
                   u.name as dosage_unit_name,
                   m.name as medicine_name, m.status as medicine_status
            FROM medicine_schedules s
            JOIN medicines m ON s.medicine_id = m.id
            JOIN LATERAL (
                SELECT * FROM medicine_schedule_versions 
                WHERE schedule_id = s.id
                ORDER BY version_number DESC LIMIT 1
            ) v ON TRUE
            JOIN dosage_units u ON v.dosage_unit_id = u.id
            WHERE m.patient_id = $1::uuid AND s.status = 'ACTIVE' AND m.status = 'ACTIVE';
        """, patient_id)
        return [dict(r) for r in rows]

    @staticmethod
    async def update_schedule_status(conn: asyncpg.Connection, schedule_id: UUID, status: str) -> None:
        await conn.execute("""
            UPDATE medicine_schedules
            SET status = $2, updated_at = now()
            WHERE id = $1::uuid;
        """, schedule_id, status)

    @staticmethod
    async def get_last_version_number(conn: asyncpg.Connection, schedule_id: UUID) -> int:
        val = await conn.fetchval("""
            SELECT MAX(version_number) FROM medicine_schedule_versions
            WHERE schedule_id = $1::uuid;
        """, schedule_id)
        return val if val is not None else 0
