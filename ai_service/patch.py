import os
import sys

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace database import
new_import = "from database import get_seats, init_db, save_alerts, get_active_alerts, get_all_alerts, resolve_alert, get_tickets_list, get_configs, update_config, get_employees, add_employee, update_employee, delete_employee, create_incident, list_incidents, get_incident, resolve_incident, get_employee\n"
content = content.replace("from database import get_seats, init_db, save_alerts, get_active_alerts, get_all_alerts, resolve_alert, get_tickets_list, get_configs, update_config, get_employees, add_employee, update_employee, delete_employee\n", new_import)

# Replace EmployeePayload
old_emp_payload = """class EmployeePayload(BaseModel):
    username: str
    password: str
    name: str
    role: str"""
new_emp_payload = """class EmployeePayload(BaseModel):
    username: str
    password: str
    name: str
    role: str
    shift: str = None"""
content = content.replace(old_emp_payload, new_emp_payload)

# Replace create_employee
old_create = """@app.post("/api/v1/employees")
def create_employee(payload: EmployeePayload):
    try:
        emp_id = add_employee(payload.username, payload.password, payload.name, payload.role)
        return {"status": "success", "id": emp_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})"""
new_create = """@app.post("/api/v1/employees")
def create_employee(payload: EmployeePayload):
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        emp_id = add_employee(payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "id": emp_id}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})"""
content = content.replace(old_create, new_create)

# Replace edit_employee
old_edit = """@app.put("/api/v1/employees/{emp_id}")
def edit_employee(emp_id: int, payload: EmployeePayload):
    try:
        update_employee(emp_id, payload.username, payload.password, payload.name, payload.role)
        return {"status": "success", "message": f"Đã cập nhật nhân viên {emp_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})"""
new_edit = """@app.put("/api/v1/employees/{emp_id}")
def edit_employee(emp_id: int, payload: EmployeePayload):
    try:
        if payload.shift:
            if payload.shift not in [s["code"] for s in SHIFTS]:
                return JSONResponse(status_code=400, content={"error": "Mã ca không hợp lệ"})
        update_employee(emp_id, payload.username, payload.password, payload.name, payload.role, payload.shift)
        return {"status": "success", "message": f"Đã cập nhật nhân viên {emp_id}"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})"""
content = content.replace(old_edit, new_edit)

# Append endpoints
append_code = """
@app.get("/api/v1/shifts")
def get_shifts():
    return {"status": "success", "shifts": SHIFTS}

@app.get("/api/v1/incident_categories")
def get_incident_categories():
    return {"status": "success", "categories": INCIDENT_CATEGORIES}

class IncidentPayload(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    room_id: str = None
    show_id: str = None
    seat_ids: list = []
    reporter_id: int
    reporter_name: str
    reporter_role: str

import datetime

@app.post("/api/v1/incidents")
def add_incident(payload: IncidentPayload):
    try:
        # Validate category
        if payload.category not in [c["code"] for c in INCIDENT_CATEGORIES]:
            return JSONResponse(status_code=400, content={"error": "Loại sự cố không hợp lệ"})
            
        from seat_mapper import normalize_seat
        normalized_seats = [normalize_seat(s) for s in payload.seat_ids]
        import json
        seat_ids_json = json.dumps(normalized_seats) if normalized_seats else ""
        
        # Determine shift label based on reporter_id
        shift_label = "Chưa phân ca"
        emp = get_employee(payload.reporter_id)
        if emp and len(emp) > 4 and emp[4]:
            shift_code = emp[4]
            for s in SHIFTS:
                if s["code"] == shift_code:
                    shift_label = s["label"]
                    break

        created_at = datetime.datetime.now().astimezone().isoformat()
        
        inc_id = create_incident(
            category=payload.category,
            severity=payload.severity,
            title=payload.title,
            description=payload.description,
            room_id=payload.room_id,
            show_id=payload.show_id,
            seat_ids=seat_ids_json,
            reporter_id=payload.reporter_id,
            reporter_name=payload.reporter_name,
            reporter_role=payload.reporter_role,
            shift_label=shift_label,
            created_at=created_at,
            status="open"
        )
        return {"status": "success", "id": inc_id, "created_at": created_at, "shift_label": shift_label}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/v1/incidents")
def fetch_incidents(room_id: str = None, status: str = None, category: str = None, from_time: str = None, to_time: str = None, limit: int = None):
    try:
        incidents = list_incidents(room_id, status, category, from_time, to_time, limit)
        return {"status": "success", "incidents": incidents}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/v1/incidents/{incident_id}")
def fetch_incident(incident_id: int):
    try:
        incident = get_incident(incident_id)
        if not incident:
            return JSONResponse(status_code=404, content={"error": "Không tìm thấy sự cố"})
        return {"status": "success", "incident": incident}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

class ResolveIncidentPayload(BaseModel):
    resolver_id: int
    resolver_name: str

@app.post("/api/v1/incidents/{incident_id}/resolve")
def resolve_incident_endpoint(incident_id: int, payload: ResolveIncidentPayload):
    try:
        resolved_at = datetime.datetime.now().astimezone().isoformat()
        resolve_incident(incident_id, payload.resolver_id, payload.resolver_name, resolved_at)
        return {"status": "success", "message": f"Đã đánh dấu sự cố {incident_id} là đã xử lý.", "resolved_at": resolved_at}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
"""

# Insert append_code right before YOLO loading
content = content.replace("print(\"[INFO] Đang tải mô hình YOLO...\")", append_code + "\nprint(\"[INFO] Đang tải mô hình YOLO...\")")

with open("main_patched.py", "w", encoding="utf-8") as f:
    f.write(content)
