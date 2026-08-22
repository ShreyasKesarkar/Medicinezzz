from datetime import date, timedelta, datetime
from uuid import UUID
from fastapi.testclient import TestClient

from app.main import app

def run_tests():
    print("Starting TestClient context (triggers startup/lifespan)...")
    
    with TestClient(app) as client:
        # Header containing our bypass test token
        headers = {
            "Authorization": "Bearer test-token-patient-1"
        }
        
        # 1. Test Auth / Profile provisioning
        print("\n--- 1. Testing Auth & Profile Auto-provisioning ---")
        response = client.get("/api/v1/me", headers=headers)
        assert response.status_code == 200, f"Auth failed: {response.text}"
        me_data = response.json()["data"]
        print("Logged in as patient:", me_data["full_name"])
        patient_id = me_data["patient_id"]
        assert me_data["user_id"] == "ccd8966a-9dda-495f-9d37-917e8a271297"
        print("Auth & Profile provisioning: PASS")

        # 2. Test Medicine & Schedule creation
        print("\n--- 2. Testing Medicine & Schedule Creation ---")
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        create_payload = {
            "name": f"Test Ibuprofen {datetime.now().microsecond}",
            "medicine_type_name": "Tablet",
            "dosage_amount": 1.5,
            "dosage_unit_name": "tablet",
            "schedule_time": "08:00",
            "frequency": "DAILY",
            "start_date": tomorrow.isoformat(),
            "planned_end_date": (tomorrow + timedelta(days=5)).isoformat(),
            "note": "Take after meals",
            "instruction_remark": "Temporary test instruction",
            "remark": "Initial test setup"
        }
        
        response = client.post("/api/v1/medicines", json=create_payload, headers=headers)
        assert response.status_code == 200, f"Creation failed: {response.text}"
        med_id = response.json()["data"]["id"]
        print("Medicine created with ID:", med_id)
        
        # Verify details
        response = client.get(f"/api/v1/medicines/{med_id}", headers=headers)
        assert response.status_code == 200
        med_details = response.json()["data"]
        assert med_details["name"] == create_payload["name"]
        assert len(med_details["schedules"]) == 1
        assert len(med_details["notes"]) == 1
        assert len(med_details["instructions"]) == 1
        print("Medicine details validation: PASS")

        # 3. Test future start dates & timeline generation
        print("\n--- 3. Testing Future Start Dates and Timeline Generation ---")
        # Timeline for today (should NOT show this medicine since it starts tomorrow)
        response = client.get(f"/api/v1/timeline?date={today.isoformat()}", headers=headers)
        assert response.status_code == 200
        today_timeline = response.json()["data"]
        # Find if today has our medicine (it shouldn't)
        for cluster in today_timeline:
            for dose in cluster["doses"]:
                assert dose["medicine_id"] != med_id, "Found medicine scheduled before its start date!"
        print("Future start date respected for today: PASS")
        
        # Timeline for tomorrow (should show this medicine)
        response = client.get(f"/api/v1/timeline?date={tomorrow.isoformat()}", headers=headers)
        assert response.status_code == 200
        tomorrow_timeline = response.json()["data"]
        
        target_dose = None
        for cluster in tomorrow_timeline:
            for dose in cluster["doses"]:
                if dose["medicine_id"] == med_id:
                    target_dose = dose
                    break
        
        assert target_dose is not None, "Medicine dose not generated on its start date (tomorrow)!"
        print("Timeline generation for tomorrow: PASS")
        assert target_dose["status"] == "PENDING"
        assert target_dose["dosage_amount"] == 1.5
        dose_id = target_dose["id"]
        print(f"Target dose ID: {dose_id} is PENDING")

        # 4. Test Dose marking taken & concurrency/double-tap prevention
        print("\n--- 4. Testing Dose Execution & Concurrency ---")
        response = client.post(f"/api/v1/doses/{dose_id}/take", json={"remark": "Dose taken!"}, headers=headers)
        assert response.status_code == 200, f"Marking taken failed: {response.text}"
        taken_data = response.json()["data"]
        assert taken_data["status"] == "TAKEN"
        assert taken_data["actual_taken_at"] is not None
        print("Dose marked as taken: PASS")
        
        # Attempt to mark taken again (concurrency check)
        response = client.post(f"/api/v1/doses/{dose_id}/take", json={"remark": "Double tap!"}, headers=headers)
        assert response.status_code == 409, "Double tap failed to raise 409 conflict!"
        print("Concurrency/Double-tap protection: PASS")

        # 5. Test Dose Correction
        print("\n--- 5. Testing Dose Corrections ---")
        correction_payload = {
            "status": "SKIPPED",
            "remark": "Accidentally marked taken"
        }
        response = client.post(f"/api/v1/doses/{dose_id}/correct", json=correction_payload, headers=headers)
        assert response.status_code == 200, f"Correction failed: {response.text}"
        corrected_data = response.json()["data"]
        assert corrected_data["status"] == "SKIPPED"
        assert corrected_data["actual_taken_at"] is None
        print("Dose status corrected to SKIPPED: PASS")

        # 6. Test Pause medicine
        print("\n--- 6. Testing Pause Medicine Lifecycle ---")
        response = client.post(f"/api/v1/medicines/{med_id}/pause", json={"remark": "Need to pause"}, headers=headers)
        assert response.status_code == 200, f"Pause failed: {response.text}"
        
        # Verify status changed
        response = client.get(f"/api/v1/medicines/{med_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "PAUSED"
        
        # Check timeline for day after tomorrow (should be NOT_REQUIRED since it is paused)
        day_after_tomorrow = tomorrow + timedelta(days=1)
        response = client.get(f"/api/v1/timeline?date={day_after_tomorrow.isoformat()}", headers=headers)
        assert response.status_code == 200
        dat_timeline = response.json()["data"]
        
        paused_dose = None
        for cluster in dat_timeline:
            for dose in cluster["doses"]:
                if dose["medicine_id"] == med_id:
                    paused_dose = dose
                    break
        assert paused_dose is not None
        assert paused_dose["status"] == "NOT_REQUIRED", f"Paused dose is not NOT_REQUIRED: {paused_dose['status']}"
        print("Pause timeline updates and notifications suppression: PASS")

        # 7. Test Resume medicine
        print("\n--- 7. Testing Resume Medicine Lifecycle ---")
        response = client.post(f"/api/v1/medicines/{med_id}/resume", headers=headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/medicines/{med_id}", headers=headers)
        assert response.json()["data"]["status"] == "ACTIVE"
        
        # Check timeline for day after tomorrow again (should regenerate as PENDING now)
        response = client.get(f"/api/v1/timeline?date={day_after_tomorrow.isoformat()}", headers=headers)
        dat_timeline_resumed = response.json()["data"]
        resumed_dose = None
        for cluster in dat_timeline_resumed:
            for dose in cluster["doses"]:
                if dose["medicine_id"] == med_id:
                    resumed_dose = dose
                    break
        assert resumed_dose is not None
        assert resumed_dose["status"] == "PENDING"
        print("Resume timeline updates: PASS")

        # 8. Test Finish medicine
        print("\n--- 8. Testing Finish Medicine Lifecycle ---")
        response = client.post(f"/api/v1/medicines/{med_id}/finish", headers=headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/medicines/{med_id}", headers=headers)
        assert response.json()["data"]["status"] == "FINISHED"
        print("Finish lifecycle transition: PASS")

        # 9. Test Undo Finish medicine
        print("\n--- 9. Testing Undo Finish Medicine Lifecycle ---")
        response = client.post(f"/api/v1/medicines/{med_id}/undo-finish", headers=headers)
        assert response.status_code == 200
        
        response = client.get(f"/api/v1/medicines/{med_id}", headers=headers)
        assert response.json()["data"]["status"] == "ACTIVE"
        print("Undo finish lifecycle transition: PASS")

        # 10. Test Audit History Logs
        print("\n--- 10. Testing History Auditing ---")
        response = client.get(f"/api/v1/history?medicine_id={med_id}", headers=headers)
        assert response.status_code == 200
        logs = response.json()["data"]
        event_types = [l["event_type"] for l in logs]
        print("Logged events found:", event_types)
        assert "MEDICINE_CREATED" in event_types
        assert "SCHEDULE_CREATED" in event_types
        assert "DOSE_TAKEN" in event_types
        assert "DOSE_CORRECTED" in event_types
        assert "PAUSE_STARTED" in event_types
        assert "MEDICINE_RESUMED" in event_types
        assert "MEDICINE_FINISHED" in event_types
        assert "FINISH_UNDONE" in event_types
        print("Audit logging validation: PASS")

    print("\n=========================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=========================")

if __name__ == "__main__":
    run_tests()
