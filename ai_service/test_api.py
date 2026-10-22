import requests

# 1. Create user duy
try:
    requests.post("http://localhost:8000/api/v1/employees", json={
        "username": "duy",
        "password": "123",
        "name": "Duy",
        "role": "nhanvien",
        "shift": "ca_sang"
    })
except Exception as e:
    pass

# 2. Get user id
emps = requests.get("http://localhost:8000/api/v1/employees").json()
duy_id = next((e["id"] for e in emps["employees"] if e["username"] == "duy"), 1)

# 3. Create incident
res = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "seat_damage",
    "severity": "high",
    "title": "Ghế rách",
    "description": "F05 rách đệm",
    "room_id": "room1",
    "show_id": "2026-10-09T18:00",
    "seat_ids": ["F05", "H01"],
    "reporter_id": duy_id,
    "reporter_name": "Duy",
    "reporter_role": "nhanvien"
})
print("CREATE INCIDENT:", res.json())

# 4. Get incidents
res2 = requests.get("http://localhost:8000/api/v1/incidents")
print("\nGET INCIDENTS:", res2.json())

# 5. Resolve incident
incident_id = res2.json()["incidents"][0]["id"]
res3 = requests.post(f"http://localhost:8000/api/v1/incidents/{incident_id}/resolve", json={
    "resolver_id": 2,
    "resolver_name": "hhh"
})
print("\nRESOLVE INCIDENT:", res3.json())

res4 = requests.get("http://localhost:8000/api/v1/incidents")
print("\nGET INCIDENTS AFTER RESOLVE:", res4.json())

# 6. Test errors
res_err1 = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "wrong_category",
    "severity": "high",
    "title": "Ghế rách",
    "description": "F05 rách đệm",
    "reporter_id": duy_id,
    "reporter_name": "Duy",
    "reporter_role": "nhanvien"
})
print("\nERROR BAD CATEGORY:", res_err1.json())

res_err2 = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "seat_damage",
    "severity": "high",
    "title": "Ghế rách",
    "description": "F05 rách đệm",
    "show_id": "2026-10-09 18:00", # missing T
    "reporter_id": duy_id,
    "reporter_name": "Duy",
    "reporter_role": "nhanvien"
})
print("\nERROR BAD SHOW_ID:", res_err2.json())

res_err3 = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "seat_damage",
    "severity": "high",
    "title": "Ghế rách",
    "description": "F05 rách đệm",
    "seat_ids": ["XXX"], # wrong seat
    "reporter_id": duy_id,
    "reporter_name": "Duy",
    "reporter_role": "nhanvien"
})
print("\nERROR BAD SEAT:", res_err3.json())

# Test user without shift
try:
    requests.post("http://localhost:8000/api/v1/employees", json={
        "username": "noshift",
        "password": "123",
        "name": "NoShift",
        "role": "nhanvien"
    })
except: pass

emps = requests.get("http://localhost:8000/api/v1/employees").json()
ns_id = next((e["id"] for e in emps["employees"] if e["username"] == "noshift"), 2)

res5 = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "seat_damage",
    "severity": "low",
    "title": "Ghế bẩn",
    "description": "F05 bẩn",
    "reporter_id": ns_id,
    "reporter_name": "NoShift",
    "reporter_role": "nhanvien"
})
print("\nNO SHIFT INCIDENT:", res5.json())

res6 = requests.get("http://localhost:8000/api/v1/incidents")
print("\nGET INCIDENTS (NO SHIFT):", res6.json()["incidents"][0])
