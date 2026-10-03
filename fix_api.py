import os

path = r'c:\CineSightApp\mobile_app\lib\core\network\api_client.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add header
new_dio = """  static final Dio _dio = Dio(
    BaseOptions(
      baseUrl: baseUrl.trim(),
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 3),
      headers: {
        'ngrok-skip-browser-warning': 'true', // Bypass ngrok free warning
      },
    ),
  );"""

old_dio = """  static final Dio _dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 3),
    ),
  );"""

content = content.replace(old_dio, new_dio)

# Clean up baseUrl space if any
content = content.replace("'https://quill-device-deny.ngrok-free.dev/  '", "'https://quill-device-deny.ngrok-free.dev'")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated api_client.dart")
