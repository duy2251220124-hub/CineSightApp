import re

with open('C:/CineSightApp/web_admin/src/pages/Alerts.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add option to dropdown
content = content.replace(
    '<option value="over_capacity">Vượt tải (Đỏ)</option>',
    '<option value="over_capacity">Vượt tải (Đỏ)</option>\n            <option value="damaged_seat">Ghế hư hỏng (Xanh)</option>'
)

# Add option with mojibake
content = content.replace(
    '<option value="over_capacity">VÆ°á»£t táº£i (Ä á» )</option>',
    '<option value="over_capacity">VÆ°á»£t táº£i (Ä á» )</option>\n            <option value="damaged_seat">Ghế hư hỏng</option>'
)

# Add logic for rendering damaged_seat
render_logic = """} else if (a.alert_type === 'damaged_seat') {
                  rowClass = 'row-warning'; 
                  label = 'Ghế hư hỏng';
                  icon = (
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 18v3h3v-3h10v3h3v-6H4v3zm15-8h3v3h-3v-3zM2 10h3v3H2v-3zm15 3H7V5c0-1.1.9-2 2-2h6c1.1 0 2 .9 2 2v8z"/></svg>
                  );
                } else {"""

content = content.replace("} else {", render_logic)

with open('C:/CineSightApp/web_admin/src/pages/Alerts.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched web_admin Alerts.jsx")
