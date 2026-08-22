import asyncpg
import json
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

class HistoryRepository:
    @staticmethod
    async def create_history(
        conn: asyncpg.Connection,
        medicine_id: UUID,
        event_type: str,
        created_by: UUID,
        schedule_id: Optional[UUID] = None,
        dose_id: Optional[UUID] = None,
        instruction_id: Optional[UUID] = None,
        note_id: Optional[UUID] = None,
        previous_data: Optional[Any] = None,
        new_data: Optional[Any] = None,
        remark: Optional[str] = None
    ) -> UUID:
        # Serialize dicts/lists to JSON string for Postgres JSONB column
        prev_json = json.dumps(previous_data) if previous_data is not None else None
        new_json = json.dumps(new_data) if new_data is not None else None
        
        h_id = await conn.fetchval("""
            INSERT INTO medicine_history (
                medicine_id, event_type, event_time, schedule_id, dose_id, 
                instruction_id, note_id, previous_data, new_data, remark, created_by
            )
            VALUES (
                $1::uuid, $2, now(), $3::uuid, $4::uuid,
                $5::uuid, $6::uuid, $7::jsonb, $8::jsonb, $9, $10::uuid
            )
            RETURNING id;
        """, medicine_id, event_type, schedule_id, dose_id,
           instruction_id, note_id, prev_json, new_json, remark, created_by)
        return h_id

    @staticmethod
    async def get_history(
        conn: asyncpg.Connection,
        patient_id: UUID,
        medicine_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
        medicine_type_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        query = """
            SELECT h.*, m.name as medicine_name, t.name as medicine_type_name
            FROM medicine_history h
            JOIN medicines m ON h.medicine_id = m.id
            LEFT JOIN medicine_types t ON m.medicine_type_id = t.id
            WHERE h.created_by = $1::uuid
        """
        params = [patient_id]
        
        if medicine_id:
            params.append(medicine_id)
            query += f" AND h.medicine_id = ${len(params)}::uuid"
            
        if event_type:
            params.append(event_type)
            query += f" AND h.event_type = ${len(params)}"

        if medicine_type_id:
            params.append(medicine_type_id)
            query += f" AND m.medicine_type_id = ${len(params)}::uuid"
            
        params.append(limit)
        limit_param = len(params)
        params.append(offset)
        offset_param = len(params)
        
        query += f" ORDER BY h.event_time DESC, h.created_at DESC LIMIT ${limit_param} OFFSET ${offset_param};"
        
        rows = await conn.fetch(query, *params)
        
        result = []
        for r in rows:
            d = dict(r)
            # Parse jsonb strings back into Python dict/list objects
            if d.get("previous_data") and isinstance(d["previous_data"], str):
                try:
                    d["previous_data"] = json.loads(d["previous_data"])
                except Exception:
                    pass
            if d.get("new_data") and isinstance(d["new_data"], str):
                try:
                    d["new_data"] = json.loads(d["new_data"])
                except Exception:
                    pass
            result.append(d)
            
        return result
