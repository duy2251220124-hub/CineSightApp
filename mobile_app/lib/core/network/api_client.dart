import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'dart:convert';
import '../database/hive_service.dart';

class ApiClient {
  // Lưu ý: Nếu chạy máy ảo Android, dùng 'http://10.0.2.2:8000'
  // Nếu cắm điện thoại thật chung WiFi, dùng 'http://192.168.111.248:8000'
  static const String baseUrl = 'http://192.168.111.248:8000';

  static final Dio _dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 3),
    ),
  );

  /// Hàm đóng gói danh sách vé quét được bắn lên AI Server
  static Future<bool> syncTicketsToServer(String roomId, String showId) async {
    try {
      final rawTickets = HiveService.getAllScannedTickets();
      if (rawTickets.isEmpty) return true; // Không có gì để đồng bộ

      List<Map<String, dynamic>> tickets = [];
      for (var raw in rawTickets) {
        try {
          final Map<String, dynamic> parsed = jsonDecode(raw);
          tickets.add({'ticket': parsed['ticket'], 'seat': parsed['seat']});
        } catch (e) {
          // Bỏ qua các chuỗi không hợp lệ
        }
      }

      final formData = FormData.fromMap({
        'room_id': roomId,
        'show_id': showId,
        'scanned_tickets': jsonEncode(tickets),
      });

      final response = await _dio.post('/api/v1/sync_tickets', data: formData);

      if (response.statusCode == 200) {
        debugPrint(
          '[NETWORK] Đồng bộ thành công ${tickets.length} vé cho phòng $roomId, suất $showId',
        );
        // Đồng bộ chỉ xóa Hive sau khi server trả 200
        await HiveService.clearTicketsAfterSync(rawTickets);
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('[NETWORK] Lỗi đồng bộ: $e');
      return false;
    }
  }
}
