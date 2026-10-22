import os
import re

main_path = "C:/CineSightApp/ai_service/main.py"
with open(main_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add SHIFTS and INCIDENT_CATEGORIES constants
constants_code = """
SHIFTS = [
    {"code": "ca_sang", "label": "Ca sáng", "start": "08:00", "end": "16:00"},
    {"code": "ca_toi", "label": "Ca tối", "start": "16:00", "end": "24:00"}
]

INCIDENT_CATEGORIES = [
    {"code": "seat_damage", "label": "Ghế hỏng"},
    {"code": "equipment", "label": "Lỗi thiết bị (máy chiếu, âm thanh...)"},
    {"code": "facility", "label": "Vệ sinh/Cơ sở vật chất"},
    {"code": "other", "label": "Khác"}
]

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
    seat_ids: list = None
    reporter_id: int
    reporter_name: str
    reporter_role: str

class ResolveIncidentPayload(BaseModel):
    resolver_id: int
    resolver_name: str

@app.post("/api/v1/incidents")
def create_incident_api(payload: IncidentPayload):
    if not any(c["code"] == payload.category for c in INCIDENT_CATEGORIES):
        return JSONResponse(status_code=400, content={"error": "Loại sự cố không hợp lệ"})
        
    if payload.show_id:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", payload.show_id):
            return JSONResponse(status_code=422, content={"error": "Định dạng show_id không hợp lệ (cần yyyy-MM-ddTHH:mm)"})
            
    normalized_seats = []
    if payload.seat_ids:
        from seat_mapper import normalize_seat
        for seat in payload.seat_ids:
            try:
                normalized_seats.append(normalize_seat(seat))
            except ValueError as e:
                return JSONResponse(status_code=422, content={"error": str(e)})
                
    import json
    import datetime
    seat_ids_json = json.dumps(normalized_seats) if normalized_seats else ""
    
    import database
    emp = database.get_employee(payload.reporter_id)
    shift_label = "Chưa phân ca"
    if emp and emp.get("shift"):
        for s in SHIFTS:
            if s["code"] == emp["shift"]:
                shift_label = s["label"]
                break
                
    created_at = datetime.datetime.now().astimezone().isoformat()
    
    try:
        incident_id = database.create_incident(
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
            status='open'
        )
        return {"status": "success", "incident_id": incident_id, "created_at": created_at}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/v1/incidents")
def get_incidents_api(
    room_id: str = None,
    status: str = None,
    category: str = None,
    from_time: str = None,
    to_time: str = None,
    limit: int = None
):
    import database
    incidents = database.list_incidents(room_id, status, category, from_time, to_time, limit)
    return {"status": "success", "incidents": incidents}

@app.get("/api/v1/incidents/{incident_id}")
def get_incident_api(incident_id: int):
    import database
    inc = database.get_incident(incident_id)
    if not inc:
        return JSONResponse(status_code=404, content={"error": "Không tìm thấy sự cố"})
    return {"status": "success", "incident": inc}

@app.post("/api/v1/incidents/{incident_id}/resolve")
def resolve_incident_api(incident_id: int, payload: ResolveIncidentPayload):
    import database
    import datetime
    inc = database.get_incident(incident_id)
    if not inc:
        return JSONResponse(status_code=404, content={"error": "Không tìm thấy sự cố"})
        
    resolved_at = datetime.datetime.now().astimezone().isoformat()
    database.resolve_incident(incident_id, payload.resolver_id, payload.resolver_name, resolved_at)
    return {"status": "success", "resolved_at": resolved_at}
"""

content = content.replace("app = FastAPI(", constants_code + "\napp = FastAPI(")

# 2. Update Employee models in main.py
old_models = """class EmployeeCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str

class EmployeeUpdate(BaseModel):
    username: str
    password: str = None
    name: str
    role: str"""

new_models = """class EmployeeCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str
    shift: str = None

class EmployeeUpdate(BaseModel):
    username: str
    password: str = None
    name: str
    role: str
    shift: str = None"""

content = content.replace(old_models, new_models)

# 3. Update add_employee and update_employee in main.py
# Let's use regex to replace add_employee logic
content = re.sub(
    r'database\.add_employee\(employee\.username, employee\.password, employee\.name, employee\.role\)',
    r'database.add_employee(employee.username, employee.password, employee.name, employee.role, employee.shift)',
    content
)

content = re.sub(
    r'database\.update_employee\(employee_id, employee\.username, employee\.password, employee\.name, employee\.role\)',
    r'database.update_employee(employee_id, employee.username, employee.password, employee.name, employee.role, employee.shift)',
    content
)

# 4. Shift validation inside add_employee api
old_add_employee_def = """@app.post("/api/v1/employees")
def add_employee_api(employee: EmployeeCreate):"""

new_add_employee_def = """@app.post("/api/v1/employees")
def add_employee_api(employee: EmployeeCreate):
    if employee.shift and not any(s["code"] == employee.shift for s in SHIFTS):
        return JSONResponse(status_code=400, content={"error": "Ca không hợp lệ"})"""

content = content.replace(old_add_employee_def, new_add_employee_def)

# Update employee update api
old_update_employee_def = """@app.put("/api/v1/employees/{employee_id}")
def update_employee_api(employee_id: int, employee: EmployeeUpdate):"""

new_update_employee_def = """@app.put("/api/v1/employees/{employee_id}")
def update_employee_api(employee_id: int, employee: EmployeeUpdate):
    if employee.shift and not any(s["code"] == employee.shift for s in SHIFTS):
        return JSONResponse(status_code=400, content={"error": "Ca không hợp lệ"})"""
        
content = content.replace(old_update_employee_def, new_update_employee_def)

# 5. Update login_user
old_login = """    cursor.execute("SELECT id, name, role FROM employees WHERE username=? AND password=?", (payload.username, payload.password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": "success", "user": {"id": row[0], "name": row[1], "role": row[2]}}"""

new_login = """    cursor.execute("SELECT id, name, role, shift FROM employees WHERE username=? AND password=?", (payload.username, payload.password))
    row = cursor.fetchone()
    conn.close()
    if row:
        shift_code = row[3]
        shift_label = "Chưa phân ca"
        if shift_code:
            for s in SHIFTS:
                if s["code"] == shift_code:
                    shift_label = s["label"]
                    break
        return {"status": "success", "user": {"id": row[0], "name": row[1], "role": row[2], "shift": shift_code, "shift_label": shift_label}}"""

content = content.replace(old_login, new_login)

with open(main_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Patched main.py")
