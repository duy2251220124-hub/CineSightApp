import 'package:dio/dio.dart';
import 'dart:convert';

class ApiClient {
  // LÆ°u Ã½: Náº¿u cháº¡y mÃ¡y áº£o Android, dÃ¹ng 'http://10.0.2.2:8000'
  // Náº¿u cáº¯m Ä‘iá»‡n thoáº¡i tháº­t, dÃ¹ng IP cá»§a mÃ¡y tÃ­nh (VD: 'http://192.168.1.15:8000')
  static const String baseUrl = 'https://quill-device-deny.ngrok-free.dev';
  
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
  ));

  /// HÃ m Ä‘Ã³ng gÃ³i danh sÃ¡ch vÃ© quÃ©t Ä‘Æ°á»£c báº¯n lÃªn AI Server
  static Future<bool> syncTicketsToServer(String roomId, List<String> tickets) async {
    try {
      final formData = FormData.fromMap({
        'room_id': roomId,
        'scanned_tickets': jsonEncode(tickets),
      });
      
      final response = await _dio.post('/api/v1/sync_tickets', data: formData);
      
      if (response.statusCode == 200) {
        print('[NETWORK] Äá»“ng bá»™ thÃ nh cÃ´ng ${tickets.length} vÃ© cho phÃ²ng $roomId');
        return true;
      }
      return false;
    } catch (e) {
      print('[NETWORK] Lá»—i Ä‘á»“ng bá»™: $e');
      return false;
    }
  }
}


