import 'package:dio/dio.dart';
import 'dart:convert';

class ApiClient {
  // Lưu ý: Nếu chạy máy ảo Android, dùng 'http://10.0.2.2:8000'
  // Nếu cắm điện thoại thật, dùng IP của máy tính (VD: 'http://192.168.1.15:8000')
  static const String baseUrl = 'http://127.0.0.1:8000';
  
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
  ));

  /// Hàm đóng gói danh sách vé quét được bắn lên AI Server
  static Future<bool> syncTicketsToServer(String roomId, List<String> tickets) async {
    try {
      final formData = FormData.fromMap({
        'room_id': roomId,
        'scanned_tickets': jsonEncode(tickets),
      });
      
      final response = await _dio.post('/api/v1/sync_tickets', data: formData);
      
      if (response.statusCode == 200) {
        print('[NETWORK] Đồng bộ thành công ${tickets.length} vé cho phòng $roomId');
        return true;
      }
      return false;
    } catch (e) {
      print('[NETWORK] Lỗi đồng bộ: $e');
      return false;
    }
  }
}
