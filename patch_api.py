import sys

with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'r', encoding='utf-8') as f:
    content = f.read()

resolve_func = '''
export const resolveAlert = async (alertId) => {
  const res = await api.post(/api/v1/resolve_alert/);
  return res.data;
};
'''

if 'resolveAlert' not in content:
    content += resolve_func
    with open(r'c:\CineSightApp\web_admin\src\api\cineSightApi.js', 'w', encoding='utf-8') as f:
        f.write(content)
