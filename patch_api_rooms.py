import sys

with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'r', encoding='utf-8') as f:
    content = f.read()

rooms_func = '''
export const getRoomsConfig = async () => {
  // TODO: Đợi Backend cung cấp API GET /api/v1/rooms
  throw new Error("API_MISSING");
};
'''

if 'getRoomsConfig' not in content:
    content += rooms_func
    with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'w', encoding='utf-8') as f:
        f.write(content)
