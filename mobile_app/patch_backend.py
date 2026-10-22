import re

with open('C:/CineSightApp/ai_service/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = """
class CreateAlertRequest(BaseModel):
    room_id: str
    show_id: str
    alert_type: str
    seats: list[str]

@app.post("/api/v1/alerts")
def create_alert(req: CreateAlertRequest):
    try:
        db.save_alerts(req.room_id, req.show_id, req.alert_type, req.seats)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

if "@app.post(\"/api/v1/alerts\")" not in content:
    content = content.replace("class ConfigRequest(BaseModel):", new_endpoint + "\nclass ConfigRequest(BaseModel):")
    with open('C:/CineSightApp/ai_service/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added create_alert endpoint")
else:
    print("Endpoint already exists")
