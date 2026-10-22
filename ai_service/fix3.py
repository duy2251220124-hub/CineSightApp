import sys
content = open('main.py', 'r', encoding='utf-8').read()
old = """        from seat_mapper import normalize_seat
        normalized_seats = [normalize_seat(s) for s in payload.seat_ids]
        import json
        seat_ids_json = json.dumps(normalized_seats) if normalized_seats else ""\n"""
new = """        import re
        if payload.show_id and not re.match(r'^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}$', payload.show_id):
            return JSONResponse(status_code=422, content={"error": "Định dạng show_id không hợp lệ (cần ISO yyyy-MM-ddTHH:mm)"})
            
        from seat_mapper import normalize_seat
        normalized_seats = []
        if payload.seat_ids:
            for s in payload.seat_ids:
                if not re.match(r'^[a-zA-Z]+\\s*\\d+$', str(s).strip()):
                    return JSONResponse(status_code=422, content={"error": f"Mã ghế '{s}' không hợp lệ"})
                normalized_seats.append(normalize_seat(s))
        import json
        seat_ids_json = json.dumps(normalized_seats) if normalized_seats else ""\n"""
content = content.replace(old, new)
open('main.py', 'w', encoding='utf-8').write(content)
