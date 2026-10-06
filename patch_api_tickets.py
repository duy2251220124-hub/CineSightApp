import sys

with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'r', encoding='utf-8') as f:
    content = f.read()

tickets_func = '''
export const getTicketsList = async (roomId, showId) => {
  // TODO: Đợi Backend cung cấp API GET /api/v1/tickets
  throw new Error("API_MISSING");
};
'''

if 'getTicketsList' not in content:
    content += tickets_func
    with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'w', encoding='utf-8') as f:
        f.write(content)
