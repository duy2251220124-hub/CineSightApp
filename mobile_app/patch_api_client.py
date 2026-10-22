import os

with open('lib/core/network/api_client.dart', 'r', encoding='utf-8') as f:
    content = f.read()

new_method = """  static Future<bool> createAlert({
    required String roomId,
    required String showId,
    required String alertType,
    required List<String> seats,
  }) async {
    try {
      final response = await _dio.post('/api/v1/alerts', data: {
        'room_id': roomId,
        'show_id': showId,
        'alert_type': alertType,
        'seats': seats,
      });
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi createAlert: $e');
      return false;
    }
  }

  static Future<bool> resolveAlert"""

if "createAlert" not in content:
    content = content.replace("static Future<bool> resolveAlert", new_method)
    with open('lib/core/network/api_client.dart', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added createAlert to API Client")
