import os

with open('lib/core/network/api_client.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_methods = """
  static Future<List<dynamic>> fetchRooms() async {
    try {
      final response = await _dio.get('/api/v1/rooms');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['rooms'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchRooms: $e');
      return [];
    }
  }

  static Future<List<dynamic>> fetchAlerts({String? roomId}) async {
    try {
      final response = await _dio.get('/api/v1/alerts', queryParameters: roomId != null ? {'room_id': roomId} : null);
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['alerts'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchAlerts: $e');
      return [];
    }
  }
  
  static Future<List<dynamic>> fetchAlertsHistory({String? roomId}) async {
    try {
      final response = await _dio.get('/api/v1/alerts/history', queryParameters: roomId != null ? {'room_id': roomId} : null);
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['alerts'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchAlertsHistory: $e');
      return [];
    }
  }

  static Future<bool> resolveAlert(int alertId) async {
    try {
      final response = await _dio.post('/api/v1/resolve_alert/$alertId');
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi resolveAlert: $e');
      return false;
    }
  }

  static Future<List<dynamic>> fetchTickets(String roomId, String showId) async {
    try {
      final response = await _dio.get('/api/v1/tickets', queryParameters: {'room_id': roomId, 'show_id': showId});
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['tickets'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchTickets: $e');
      return [];
    }
  }
"""

# Insert before the last closing brace
for i in range(len(lines)-1, -1, -1):
    if lines[i].strip() == '}':
        lines.insert(i, new_methods)
        break

with open('lib/core/network/api_client.dart', 'w', encoding='utf-8') as f:
    f.writelines(lines)
