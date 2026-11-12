import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Một bản ghi lịch sử quét vé (lưu vĩnh viễn trên máy, KHÔNG bị xóa khi sync).
class ScanRecord {
  final String ticket;
  final String room;
  final String seat;
  final String show;
  final DateTime scannedAt;

  const ScanRecord({
    required this.ticket,
    required this.room,
    required this.seat,
    required this.show,
    required this.scannedAt,
  });

  Map<String, dynamic> toJson() => {
        'ticket': ticket,
        'room': room,
        'seat': seat,
        'show': show,
        'scanned_at': scannedAt.toIso8601String(),
      };

  static ScanRecord? tryParse(String raw) {
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return ScanRecord(
        ticket: '${map['ticket']}',
        room: '${map['room'] ?? ''}',
        seat: '${map['seat'] ?? ''}',
        show: '${map['show'] ?? ''}',
        scannedAt: DateTime.tryParse('${map['scanned_at']}') ?? DateTime.now(),
      );
    } catch (_) {
      return null;
    }
  }
}

class HiveService {
  static const String _ticketBoxName = 'scanned_tickets_box';

  /// Hộp lịch sử: giữ lại mọi vé đã quét để chống quét trùng sau khi sync
  /// và để hiển thị màn "Lịch sử quét vé". Key = mã vé.
  static const String _historyBoxName = 'scan_history_box';

  /// Hộp cài đặt cấu hình ứng dụng (Server URL, v.v.)
  static const String _settingsBoxName = 'app_settings_box';

  /// URL máy chủ mặc định (fallback khi chưa lưu cấu hình)
  static const String defaultServerUrl = 'https://quill-device-deny.ngrok-free.dev';

  /// Trạng thái chế độ Sáng (Light Mode = true) / Tối (Dark Mode = false)
  static final ValueNotifier<bool> lightModeNotifier = ValueNotifier<bool>(true);

  /// Bộ đếm phiên bản ảnh đại diện để cập nhật tức thì giữa các màn hình
  static final ValueNotifier<int> avatarRevision = ValueNotifier<int>(0);

  /// Kiểm tra hiện tại đang ở Light Mode hay không
  static bool get isLightMode => lightModeNotifier.value;

  /// Khởi tạo Hive Database (Chạy 1 lần duy nhất khi mở App)
  static Future<void> init() async {
    // Khởi tạo engine lưu trữ trên điện thoại
    await Hive.initFlutter();

    // Mở các "Hộp" để chứa dữ liệu
    await Hive.openBox<String>(_ticketBoxName);
    await Hive.openBox<String>(_historyBoxName);
    final settingsBox = await Hive.openBox<String>(_settingsBoxName);
    final savedTheme = settingsBox.get('is_light_mode');
    lightModeNotifier.value = savedTheme == null ? true : (savedTheme == 'true');
    if (settingsBox.get('device_id') == null) {
      final rand = DateTime.now().microsecondsSinceEpoch.toRadixString(36);
      await settingsBox.put('device_id', 'mobile_$rand');
    }
  }

  /// Lấy mã định danh thiết bị duy nhất (phục vụ phát hiện quét trùng đa thiết bị UC04)
  static String getDeviceId() {
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) return 'mobile_default';
      final box = Hive.box<String>(_settingsBoxName);
      return box.get('device_id') ?? 'mobile_default';
    } catch (_) {
      return 'mobile_default';
    }
  }

  /// Chuyển đổi chế độ Sáng (true) / Tối (false) và lưu vào bộ nhớ máy
  static Future<void> setLightMode(bool isLight) async {
    lightModeNotifier.value = isLight;
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) {
        await Hive.openBox<String>(_settingsBoxName);
      }
      final box = Hive.box<String>(_settingsBoxName);
      await box.put('is_light_mode', isLight ? 'true' : 'false');
    } catch (e) {
      debugPrint('[HIVE] Error setting light mode: $e');
    }
  }

  /// Lấy địa chỉ máy chủ hiện tại
  static String getServerUrl() {
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) return defaultServerUrl;
      final box = Hive.box<String>(_settingsBoxName);
      final saved = box.get('server_url');
      if (saved != null && saved.trim().isNotEmpty) {
        return saved.trim();
      }
    } catch (e) {
      debugPrint('[HIVE] Error getting server url: $e');
    }
    return defaultServerUrl;
  }

  /// Cập nhật địa chỉ máy chủ
  static Future<void> setServerUrl(String url) async {
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) {
        await Hive.openBox<String>(_settingsBoxName);
      }
      final box = Hive.box<String>(_settingsBoxName);
      var clean = url.trim();
      if (clean.endsWith('/')) {
        clean = clean.substring(0, clean.length - 1);
      }
      await box.put('server_url', clean);
      debugPrint('[HIVE] Đã lưu Server URL mới: $clean');
    } catch (e) {
      debugPrint('[HIVE] Error setting server url: $e');
    }
  }

  /// Lấy ảnh đại diện (Base64) đã lưu của nhân viên
  static String? getEmployeeAvatar(String userKey) {
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) return null;
      final box = Hive.box<String>(_settingsBoxName);
      final cleanKey = 'avatar_${userKey.trim().toLowerCase()}';
      final saved = box.get(cleanKey);
      if (saved != null && saved.trim().isNotEmpty) {
        return saved.trim();
      }
    } catch (e) {
      debugPrint('[HIVE] Error getting avatar: $e');
    }
    return null;
  }

  /// Lưu hoặc xóa ảnh đại diện (Base64) của nhân viên
  static Future<void> setEmployeeAvatar(String userKey, String? base64Data) async {
    try {
      if (!Hive.isBoxOpen(_settingsBoxName)) {
        await Hive.openBox<String>(_settingsBoxName);
      }
      final box = Hive.box<String>(_settingsBoxName);
      final cleanKey = 'avatar_${userKey.trim().toLowerCase()}';
      if (base64Data == null || base64Data.trim().isEmpty) {
        await box.delete(cleanKey);
      } else {
        await box.put(cleanKey, base64Data.trim());
      }
      avatarRevision.value++;
    } catch (e) {
      debugPrint('[HIVE] Error setting avatar: $e');
    }
  }

  /// Đếm số lượng vé tồn đọng chưa được đồng bộ lên máy chủ
  static int getPendingTicketsCount() {
    try {
      if (!Hive.isBoxOpen(_ticketBoxName)) return 0;
      return Hive.box<String>(_ticketBoxName).length;
    } catch (_) {
      return 0;
    }
  }

  /// Ghi lịch sử quét (key = mã vé nên mỗi vé chỉ có 1 bản ghi).
  static Future<void> addScanRecord(ScanRecord record) async {
    final box = Hive.box<String>(_historyBoxName);
    await box.put(record.ticket, jsonEncode(record.toJson()));
  }

  /// Tìm bản ghi quét trước đó của 1 mã vé (null nếu chưa quét).
  static ScanRecord? findScanRecord(String ticket) {
    final raw = Hive.box<String>(_historyBoxName).get(ticket);
    return raw == null ? null : ScanRecord.tryParse(raw);
  }

  /// Tìm bản ghi quét trước đó theo vị trí ghế trong cùng phòng & suất chiếu.
  static ScanRecord? findScanRecordBySeat(String room, String show, String seat) {
    final normSeat = seat.trim().toUpperCase();
    for (final raw in Hive.box<String>(_historyBoxName).values) {
      final rec = ScanRecord.tryParse(raw);
      if (rec != null &&
          rec.room == room &&
          rec.show == show &&
          rec.seat.trim().toUpperCase() == normSeat) {
        return rec;
      }
    }
    return null;
  }

  /// Lịch sử quét, mới nhất trước. Lọc theo phòng / suất nếu truyền vào.
  static List<ScanRecord> getScanHistory({String? roomId, String? showId}) {
    final records = Hive.box<String>(_historyBoxName)
        .values
        .map(ScanRecord.tryParse)
        .whereType<ScanRecord>()
        .where((r) => roomId == null || roomId.isEmpty || r.room == roomId)
        .where((r) => showId == null || showId.isEmpty || showId == 'all' || r.show == showId)
        .toList()
      ..sort((a, b) => b.scannedAt.compareTo(a.scannedAt));
    return records;
  }

  /// Hàm lưu mã vé vừa quét vào bộ nhớ máy (Dành cho lúc rớt mạng)
  static Future<void> saveScannedTicket(String ticketCode) async {
    final box = Hive.box<String>(_ticketBoxName);

    // Thuật toán chống lưu trùng lặp: Nếu trong máy chưa có vé này thì mới lưu
    if (!box.values.contains(ticketCode)) {
      await box.add(ticketCode);
      debugPrint('[HIVE] Đã lưu vé $ticketCode vào bộ nhớ Offline thành công!');
    }
  }

  /// Lấy danh sách toàn bộ vé đang lưu trong máy để chuẩn bị đẩy lên AI Server
  static List<String> getAllScannedTickets() {
    final box = Hive.box<String>(_ticketBoxName);
    return box.values.toList();
  }

  /// Xóa toàn bộ vé trong máy SAU KHI đã đồng bộ lên mạng thành công
  static Future<void> clearTicketsAfterSync(List<String> syncedTickets) async {
    final box = Hive.box<String>(_ticketBoxName);
    final keysToDelete = [];
    for (var key in box.keys) {
      if (syncedTickets.contains(box.get(key))) {
        keysToDelete.add(key);
      }
    }
    await box.deleteAll(keysToDelete);
    debugPrint('[HIVE] Đã dọn dẹp ${keysToDelete.length} vé khỏi bộ nhớ Offline sau khi đồng bộ!');
  }

  /// Xóa toàn bộ lịch sử quét vé trên thiết bị để chuẩn bị cho đợt kiểm thử mới
  static Future<void> clearAllHistory() async {
    final historyBox = Hive.box<String>(_historyBoxName);
    final ticketBox = Hive.box<String>(_ticketBoxName);
    await historyBox.clear();
    await ticketBox.clear();
    debugPrint('[HIVE] Đã làm trống toàn bộ lịch sử quét vé!');
  }
}
