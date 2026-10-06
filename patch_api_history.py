import sys

with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'r', encoding='utf-8') as f:
    content = f.read()

history_func = '''
export const getAlertHistory = async (roomId, alertType, status) => {
  // TODO: Ä á»£i Backend cung cáº¥p API GET /api/v1/alerts/history
  // Táº¡m thá» i tráº£ vá»  mÃ£ lá»—i Ä‘á»ƒ UI hiá»ƒn thá»‹ tráº¡ng thÃ¡i trá»‘ng
  throw new Error("API_MISSING");
};
'''

if 'getAlertHistory' not in content:
    content += history_func
    with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'w', encoding='utf-8') as f:
        f.write(content)
