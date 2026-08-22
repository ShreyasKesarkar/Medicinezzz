import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import db

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    
    # Bypass for testing environment or special test token
    if token == "test-token-patient-1" or token == "ccd8966a-9dda-495f-9d37-917e8a271297":
        return {
            "id": "ccd8966a-9dda-495f-9d37-917e8a271297",
            "email": "test@example.com",
            "user_metadata": {"full_name": "Test Patient"}
        }
    if token == "test-token-patient-2" or token == "625d65a8-4afa-4e8f-954f-6fd3dc6c14e0":
        return {
            "id": "625d65a8-4afa-4e8f-954f-6fd3dc6c14e0",
            "email": "tungsten@example.com",
            "user_metadata": {"full_name": "tungsten7876"}
        }
        
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.supabase_url}/auth/v1/user",
                headers=headers
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token or unauthorized session"
                )
            user_data = response.json()
            return user_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

async def get_current_patient(
    user_data: dict = Depends(get_current_user),
    conn = Depends(db.get_conn)
) -> dict:
    user_id = user_data["id"]
    email = user_data.get("email", "")
    full_name = user_data.get("user_metadata", {}).get("full_name", email.split("@")[0] if email else "User")
    
    # Check if patient exists
    row = await conn.fetchrow("""
        SELECT p.id as patient_id, u.id as user_id, u.full_name, u.timezone
        FROM user_profiles u
        JOIN patients p ON p.user_id = u.id
        WHERE u.id = $1::uuid;
    """, user_id)
    
    if row:
        return {
            "patient_id": str(row["patient_id"]),
            "user_id": str(row["user_id"]),
            "full_name": row["full_name"],
            "timezone": row["timezone"]
        }
        
    # Auto-provision profile and patient records
    try:
        # Create user profile if not exists
        await conn.execute("""
            INSERT INTO user_profiles (id, full_name, timezone)
            VALUES ($1::uuid, $2, 'Asia/Kolkata')
            ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;
        """, user_id, full_name)
        
        # Create patient if not exists
        p_id = await conn.fetchval("""
            INSERT INTO patients (user_id)
            VALUES ($1::uuid)
            ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id
            RETURNING id;
        """, user_id)
        
        return {
            "patient_id": str(p_id),
            "user_id": str(user_id),
            "full_name": full_name,
            "timezone": "Asia/Kolkata"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-provision patient profile: {str(e)}"
        )
