import requests

requests.post("http://localhost:8000/api/v1/employees", json={
    "username": "duy_shift",
    "password": "123",
    "name": "Duy Shift",
    "role": "nhanvien",
    "shift": "ca_sang"
})

emps = requests.get("http://localhost:8000/api/v1/employees").json()
ds_id = next((e["id"] for e in emps["employees"] if e["username"] == "duy_shift"), None)

res = requests.post("http://localhost:8000/api/v1/incidents", json={
    "category": "seat_damage",
    "severity": "high",
    "title": "Ghế rách",
    "description": "F05 rách đệm",
    "reporter_id": ds_id,
    "reporter_name": "Duy Shift",
    "reporter_role": "nhanvien"
})
print(res.json())
