import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:crypto/crypto.dart';

import 'dart:convert';

import '../database/hive_service.dart';

class ApiClient {
  static String get baseUrl => HiveService.getServerUrl();

  /// Khóa bí mật HMAC-SHA256 dùng để xác thực chữ ký số mã QR vé ngay cả khi Offline 100% (UC03/UC04)
  static const String qrHmacSecret = 'CINESIGHT_QR_HMAC_2026_SECRET_KEY';
  static const Set<String> vipRows = {'F', 'G', 'H', 'I', 'J'};

  /// Chuẩn hóa mã ghế (A1 -> A01)
  static String normalizeSeatCode(String seat) {
    final clean = seat.trim().toUpperCase();
    if (clean.length == 2 &&
        clean.codeUnitAt(1) >= 48 &&
        clean.codeUnitAt(1) <= 57) {
      return '${clean[0]}0${clean[1]}';
    }
    return clean;
  }

  /// Xác định hạng ghế: VIP (hàng F, G, H, I, J) hoặc STANDARD (hàng A..E, K, L)
  static String getSeatTier(String seat) {
    final clean = normalizeSeatCode(seat);
    if (clean.isEmpty) return 'STANDARD';
    return vipRows.contains(clean[0]) ? 'VIP' : 'STANDARD';
  }

  /// Tạo chữ ký số HMAC-SHA256 (16 ký tự hex đầu) khớp với backend security.py
  static String signTicketQr({
    required String room,
    required String show,
    required String ticket,
    required String seat,
  }) {
    final cleanRoom = room.replaceAll('seats_config_', '').trim();
    final cleanShow = show.trim();
    final cleanTicket = ticket.trim();
    final cleanSeat = normalizeSeatCode(seat);
    final canonical = '$cleanRoom|$cleanShow|$cleanTicket|$cleanSeat';
    final hmac = Hmac(sha256, utf8.encode(qrHmacSecret));
    final digest = hmac.convert(utf8.encode(canonical)).toString();
    return digest.substring(0, 16);
  }

  /// Kiểm tra chữ ký số HMAC-SHA256 trên mã QR vé (chống vé giả mạo Offline & Online)
  static bool verifyTicketQrSignature({
    required String room,
    required String show,
    required String ticket,
    required String seat,
    required String? signature,
  }) {
    if (signature == null || signature.trim().isEmpty) return false;
    final cleanSig = signature.trim().toLowerCase();
    final expected = signTicketQr(
      room: room,
      show: show,
      ticket: ticket,
      seat: seat,
    ).toLowerCase();
    return cleanSig == expected;
  }

  /// Danh sách xung đột quét trùng đa thiết bị từ lần đồng bộ gần nhất
  static List<Map<String, dynamic>> lastSyncConflicts = [];

  /// Cập nhật địa chỉ máy chủ động mà không cần build lại APK
  static void updateBaseUrl(String newUrl) {
    HiveService.setServerUrl(newUrl);
    _dio.options.baseUrl = HiveService.getServerUrl();
  }

  static Map<String, dynamic>? currentUser;
  static String? authToken;
  static String? lastLoginError;

  static void logout() {
    currentUser = null;
    authToken = null;
    _dio.options.headers.remove('Authorization');
  }

  /// Nhận diện ca trực tự động phủ kín 24h kèm khoảng đệm ±30 phút (UC01)
  static String getDynamicShiftLabel(
    String? role, [
    DateTime? time,
    String? assignedShift,
  ]) {
    final now = time ?? DateTime.now();
    final minuteOfDay = now.hour * 60 + now.minute;
    final r = (role ?? '').trim().toLowerCase();
    final isManager =
        r.contains('quản lý') || r.contains('manager') || r.contains('admin');

    final assigned =
        (assignedShift ?? currentUser?['shift']?.toString() ?? '').trim();

    if (isManager) {
      if (assigned == 'ca_sang' && minuteOfDay >= 420 && minuteOfDay <= 990) {
        return 'Ca sáng (07:30 - 16:00)';
      }
      if (assigned == 'ca_toi' && minuteOfDay >= 930 && minuteOfDay <= 1440) {
        return 'Ca tối (16:00 - 24:00)';
      }
      // Đệm 30 phút đầu ngày (07:00 - 07:30) và lấp khoảng trống 16:00 - 16:30
      if (minuteOfDay >= 420 && minuteOfDay < 960) {
        return 'Ca sáng (07:30 - 16:00)';
      } else if (minuteOfDay >= 960 && minuteOfDay < 1440) {
        return 'Ca tối (16:00 - 24:00)';
      } else {
        return 'Ca đêm (00:00 - 07:30)';
      }
    } else {
      if (assigned == 'ca_sang' && minuteOfDay >= 420 && minuteOfDay <= 810) {
        return 'Ca sáng (07:30 - 13:00)';
      }
      if (assigned == 'ca_chieu' && minuteOfDay >= 750 && minuteOfDay <= 990) {
        return 'Ca chiều (13:00 - 16:00)';
      }
      if (assigned == 'ca_toi' && minuteOfDay >= 930 && minuteOfDay <= 1410) {
        return 'Ca tối (16:00 - 23:00)';
      }
      // Đệm 30 phút trước ca sáng (07:00) và 30 phút bàn giao sau ca tối (23:30)
      if (minuteOfDay >= 420 && minuteOfDay < 780) {
        return 'Ca sáng (07:30 - 13:00)';
      } else if (minuteOfDay >= 780 && minuteOfDay < 960) {
        return 'Ca chiều (13:00 - 16:00)';
      } else if (minuteOfDay >= 960 && minuteOfDay <= 1410) {
        return 'Ca tối (16:00 - 23:00)';
      } else {
        return 'Ca đêm (23:00 - 07:30)';
      }
    }
  }

  static Future<bool> login(String username, String password) async {
    final cleanUser = username.trim();
    final cleanPass = password.trim();
    if (cleanUser.isEmpty || cleanPass.isEmpty) {
      lastLoginError = 'Vui lòng nhập đầy đủ tài khoản và mật khẩu';
      return false;
    }
    try {
      final response = await _dio.post(
        '/api/v1/login',
        data: {'username': cleanUser, 'password': cleanPass},
      );
      if (response.statusCode == 200) {
        currentUser = response.data['user'];
        authToken = response.data['token']?.toString();
        if (authToken != null && authToken!.isNotEmpty) {
          _dio.options.headers['Authorization'] = 'Bearer $authToken';
        }
        lastLoginError = null;
        return true;
      }
      lastLoginError = response.data?['error']?.toString() ?? 'Lỗi đăng nhập';
      return false;
    } on DioException catch (e) {
      if (e.response != null &&
          e.response?.data is Map &&
          e.response?.data['error'] != null) {
        lastLoginError = e.response?.data['error'].toString();
      } else if (e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        lastLoginError = 'Kết nối mạng quá chậm, vui lòng thử lại';
      } else {
        lastLoginError = 'Không thể kết nối đến máy chủ (kiểm tra Ngrok)';
      }
      debugPrint('[NETWORK] Login error: ${e.message}');
      return false;
    } catch (e) {
      lastLoginError = 'Lỗi kết nối: $e';
      debugPrint('[NETWORK] Login error: $e');
      return false;
    }
  }

  static final Dio _dio =
      Dio(
          BaseOptions(
            baseUrl: HiveService.getServerUrl(),
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 15),
            headers: {
              'ngrok-skip-browser-warning': 'true', // Bypass ngrok free warning
            },
          ),
        )
        ..interceptors.add(
          InterceptorsWrapper(
            onRequest: (options, handler) {
              if (authToken != null && authToken!.isNotEmpty) {
                options.headers['Authorization'] = 'Bearer $authToken';
              }
              handler.next(options);
            },
          ),
        );

  /// Hàm đóng gói danh sách vé quét được bắn lên AI Server (kèm chữ ký số & device_id)
  static Future<bool> syncTicketsToServer(String roomId, String showId) async {
    try {
      final rawTickets = HiveService.getAllScannedTickets();
      if (rawTickets.isEmpty) return true; // Không có gì để đồng bộ

      final Map<String, Map<String, List<Map<String, dynamic>>>> groups = {};
      final Map<String, Map<String, List<String>>> groupRawTickets = {};
      final deviceId = HiveService.getDeviceId();
      lastSyncConflicts = [];

      for (var raw in rawTickets) {
        try {
          final Map<String, dynamic> parsed = jsonDecode(raw);
          final ticketRoom = parsed['room']?.toString() ?? roomId;
          final ticketShow = parsed['show']?.toString() ?? showId;
          final seatStr = parsed['seat']?.toString() ?? '';

          groups.putIfAbsent(ticketRoom, () => {});
          groups[ticketRoom]!.putIfAbsent(ticketShow, () => []);
          groups[ticketRoom]![ticketShow]!.add({
            'ticket': parsed['ticket'],
            'seat': seatStr,
            'tier': parsed['tier'] ?? getSeatTier(seatStr),
            'sig': parsed['sig'] ?? parsed['signature'],
            'device_id': deviceId,
          });

          groupRawTickets.putIfAbsent(ticketRoom, () => {});
          groupRawTickets[ticketRoom]!.putIfAbsent(ticketShow, () => []);
          groupRawTickets[ticketRoom]![ticketShow]!.add(raw);
        } catch (e) {
          // Bỏ qua các chuỗi không hợp lệ
        }
      }

      bool allSuccess = true;
      List<String> successfullySyncedRawTickets = [];

      for (var rId in groups.keys) {
        for (var sId in groups[rId]!.keys) {
          final tickets = groups[rId]![sId]!;
          final rawList = groupRawTickets[rId]![sId]!;

          final formData = FormData.fromMap({
            'room_id': rId,
            'show_id': sId,
            'device_id': deviceId,
            'scanned_tickets': jsonEncode(tickets),
          });

          try {
            final response = await _dio.post(
              '/api/v1/sync_tickets',
              data: formData,
            );
            if (response.statusCode == 200) {
              debugPrint(
                '[NETWORK] Đồng bộ thành công ${tickets.length} vé cho phòng $rId, suất $sId',
              );
              final conflicts = response.data?['conflicts'];
              if (conflicts is List && conflicts.isNotEmpty) {
                for (final c in conflicts) {
                  if (c is Map) {
                    lastSyncConflicts.add(Map<String, dynamic>.from(c));
                  }
                }
              }
              successfullySyncedRawTickets.addAll(rawList);
            } else {
              allSuccess = false;
            }
          } catch (e) {
            debugPrint('[NETWORK] Lỗi đồng bộ phòng $rId suất $sId: $e');
            allSuccess = false;
          }
        }
      }

      if (successfullySyncedRawTickets.isNotEmpty) {
        await HiveService.clearTicketsAfterSync(successfullySyncedRawTickets);
      }

      return allSuccess;
    } catch (e) {
      debugPrint('[NETWORK] Lỗi đồng bộ chung: $e');
      return false;
    }
  }

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

  static Future<List<dynamic>> fetchShowtimes({
    String? roomId,
    String? date,
  }) async {
    try {
      final params = <String, dynamic>{};
      if (roomId != null && roomId.isNotEmpty) params['room_id'] = roomId;
      if (date != null && date.isNotEmpty) params['date'] = date;
      final response = await _dio.get(
        '/api/v1/showtimes',
        queryParameters: params.isEmpty ? null : params,
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['showtimes'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchShowtimes: $e');
      return [];
    }
  }

  static Future<List<dynamic>> fetchAlerts({String? roomId}) async {
    try {
      final response = await _dio.get(
        '/api/v1/alerts',
        queryParameters: roomId != null ? {'room_id': roomId} : null,
      );
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
      final response = await _dio.get(
        '/api/v1/alerts/history',
        queryParameters: roomId != null ? {'room_id': roomId} : null,
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['alerts'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchAlertsHistory: $e');
      return [];
    }
  }

  static Future<bool> createAlert({
    required String roomId,
    required String showId,
    required String alertType,
    required List<String> seats,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/alerts',
        data: {
          'room_id': roomId,
          'show_id': showId,
          'alert_type': alertType,
          'seats': seats,
        },
      );
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi createAlert: $e');
      return false;
    }
  }

  static Future<bool> resolveAlert(
    int alertId, {
    String resolution = 'violation_handled',
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/resolve_alert/$alertId',
        data: {'resolution': resolution},
      );
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi resolveAlert: $e');
      return false;
    }
  }

  /// Xử lý hàng loạt toàn bộ cảnh báo của 1 phòng chiếu (One-Tap Batch Resolve)
  /// resolution: 'violation_handled' (mời về đúng ghế/ra ngoài) | 'ticket_verified' (bổ sung ghế vào Tập A)
  static Future<bool> resolveRoomAlerts(
    String roomId,
    String showId, {
    String resolution = 'violation_handled',
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/resolve_room_alerts',
        data: {
          'room_id': roomId,
          'show_id': showId,
          'resolution': resolution,
        },
      );
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi resolveRoomAlerts: $e');
      return false;
    }
  }

  static Future<List<dynamic>> fetchGroupedAlerts({String? roomId}) async {
    try {
      final response = await _dio.get(
        '/api/v1/alerts',
        queryParameters: roomId != null ? {'room_id': roomId} : null,
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['grouped_alerts'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchGroupedAlerts: $e');
      return [];
    }
  }

  static Future<List<dynamic>> fetchTickets(
    String roomId,
    String showId,
  ) async {
    try {
      final response = await _dio.get(
        '/api/v1/tickets',
        queryParameters: {'room_id': roomId, 'show_id': showId},
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['tickets'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi fetchTickets: $e');
      return [];
    }
  }

  static Future<Map<String, dynamic>> createIncident({
    required String category,
    required String severity,
    required String title,
    required String description,
    String? roomId,
    String? showId,
    List<String> seatIds = const [],
  }) async {
    try {
      if (currentUser == null) throw Exception("Bạn chưa đăng nhập");

      final response = await _dio.post(
        '/api/v1/incidents',
        data: {
          'category': category,
          'severity': severity,
          'title': title,
          'description': description,
          'room_id': roomId,
          'show_id': showId,
          'seat_ids': seatIds,
          'reporter_id': currentUser!['id'],
          'reporter_name': currentUser!['name'],
          'reporter_role': currentUser!['role'],
        },
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return {'success': true, 'data': response.data};
      }
      return {
        'success': false,
        'error': response.data['error'] ?? 'Lỗi không xác định',
      };
    } on DioException catch (e) {
      debugPrint('[NETWORK] Lỗi createIncident: $e');
      return {
        'success': false,
        'error': e.response?.data?['error'] ?? 'Lỗi kết nối máy chủ',
      };
    } catch (e) {
      debugPrint('[NETWORK] Lỗi createIncident: $e');
      return {'success': false, 'error': e.toString()};
    }
  }

  /// Chuyển đổi đường dẫn ảnh tương đối thành URL đầy đủ
  static String getImageUrl(String? path) {
    if (path == null || path.trim().isEmpty) return '';
    final clean = path.trim();
    if (clean.startsWith('http://') || clean.startsWith('https://')) {
      return clean;
    }
    final base = baseUrl.replaceAll(RegExp(r'/+$'), '');
    final prefix = clean.startsWith('/') ? '' : '/';
    return '$base$prefix$clean';
  }

  static Future<bool> uploadIncidentPhoto(
    int incidentId,
    dynamic fileOrBytes, {
    String? filename,
  }) async {
    try {
      MultipartFile multipartFile;
      if (fileOrBytes is Uint8List) {
        multipartFile = MultipartFile.fromBytes(
          fileOrBytes,
          filename: filename ?? ('incident_$incidentId.jpg'),
        );
      } else if (fileOrBytes is List<int>) {
        multipartFile = MultipartFile.fromBytes(
          Uint8List.fromList(fileOrBytes),
          filename: filename ?? ('incident_$incidentId.jpg'),
        );
      } else if (kIsWeb) {
        debugPrint(
          '[NETWORK] Trên Web bắt buộc phải truyền byte ảnh (Uint8List)',
        );
        return false;
      } else {
        final pathStr = fileOrBytes.toString();
        final fname = filename ?? pathStr.split(RegExp(r'[/\\]')).last;
        multipartFile = await MultipartFile.fromFile(pathStr, filename: fname);
      }
      final formData = FormData.fromMap({'image': multipartFile});
      final response = await _dio.post(
        '/api/v1/incidents/$incidentId/photo',
        data: formData,
      );
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi uploadIncidentPhoto: $e');
      return false;
    }
  }

  static Future<List<dynamic>> getIncidents({
    String? roomId,
    String? status,
    String? category,
    int? limit,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (roomId != null) queryParams['room_id'] = roomId;
      if (status != null) queryParams['status'] = status;
      if (category != null) queryParams['category'] = category;
      if (limit != null) queryParams['limit'] = limit;

      final response = await _dio.get(
        '/api/v1/incidents',
        queryParameters: queryParams,
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['incidents'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi getIncidents: $e');
      return [];
    }
  }

  static Future<Map<String, dynamic>?> getIncident(int id) async {
    try {
      final response = await _dio.get('/api/v1/incidents/$id');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['incident'];
      }
      return null;
    } catch (e) {
      debugPrint('[NETWORK] Lỗi getIncident: $e');
      return null;
    }
  }

  static Future<Map<String, dynamic>> resolveIncident(int incidentId) async {
    try {
      if (currentUser == null) throw Exception("Bạn chưa đăng nhập");

      final response = await _dio.post(
        '/api/v1/incidents/$incidentId/resolve',
        data: {
          'resolver_id': currentUser!['id'],
          'resolver_name': currentUser!['name'],
        },
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return {'success': true, 'data': response.data};
      }
      return {
        'success': false,
        'error': response.data['error'] ?? 'Lỗi không xác định',
      };
    } on DioException catch (e) {
      debugPrint('[NETWORK] Lỗi resolveIncident: $e');
      return {
        'success': false,
        'error': e.response?.data?['error'] ?? 'Lỗi kết nối máy chủ',
      };
    } catch (e) {
      debugPrint('[NETWORK] Lỗi resolveIncident: $e');
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<List<dynamic>> getIncidentCategories() async {
    try {
      final response = await _dio.get('/api/v1/incident_categories');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return response.data['categories'] ?? [];
      }
      return [];
    } catch (e) {
      debugPrint('[NETWORK] Lỗi getIncidentCategories: $e');
      return [];
    }
  }

  static Future<Map<String, dynamic>> deleteIncident(int incidentId) async {
    try {
      final response = await _dio.delete('/api/v1/incidents/$incidentId');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return {'success': true, 'data': response.data};
      }
      return {
        'success': false,
        'error': response.data['error'] ?? 'Lỗi không xác định',
      };
    } catch (e) {
      debugPrint('[NETWORK] Lỗi deleteIncident: $e');
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<bool> clearResolvedIncidents() async {
    try {
      final response = await _dio.delete('/api/v1/incidents/resolved/clear');
      return response.statusCode == 200 && response.data['status'] == 'success';
    } catch (e) {
      debugPrint('[NETWORK] Lỗi clearResolvedIncidents: $e');
      return false;
    }
  }
}
