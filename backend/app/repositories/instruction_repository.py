import asyncpg
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class InstructionRepository:
    @staticmethod
    async def create_instruction(
        conn: asyncpg.Connection,
        medicine_id: UUID,
        instruction_type: str,
        effective_from: datetime,
        effective_until: Optional[datetime],
        remark: Optional[str],
        created_by: UUID
    ) -> UUID:
        i_id = await conn.fetchval("""
            INSERT INTO medication_instructions (
                medicine_id, instruction_type, effective_from, effective_until, remark, created_by
            )
            VALUES ($1::uuid, $2, $3, $4, $5, $6::uuid)
            RETURNING id;
        """, medicine_id, instruction_type, effective_from, effective_until, remark, created_by)
        return i_id

    @staticmethod
    async def get_instructions_by_medicine(conn: asyncpg.Connection, medicine_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT * FROM medication_instructions
            WHERE medicine_id = $1::uuid
            ORDER BY created_at DESC;
        """, medicine_id)
        return [dict(r) for r in rows]

    @staticmethod
    async def create_note(
        conn: asyncpg.Connection,
        medicine_id: UUID,
        note: str,
        created_by: UUID
    ) -> UUID:
        n_id = await conn.fetchval("""
            INSERT INTO medicine_notes (medicine_id, note, created_by)
            VALUES ($1::uuid, $2, $3::uuid)
            RETURNING id;
        """, medicine_id, note, created_by)
        return n_id

    @staticmethod
    async def get_notes_by_medicine(conn: asyncpg.Connection, medicine_id: UUID) -> List[dict]:
        rows = await conn.fetch("""
            SELECT * FROM medicine_notes
            WHERE medicine_id = $1::uuid
            ORDER BY created_at DESC;
        """, medicine_id)
        return [dict(r) for r in rows]
