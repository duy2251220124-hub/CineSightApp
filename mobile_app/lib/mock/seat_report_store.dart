import 'package:flutter/foundation.dart';

/// Trạng thái dùng chung (in-memory) cho luồng "Báo ghế hư".
///
/// - [selected]: các ghế người dùng đang chạm chọn (màu cam + viền trắng).
///   Dùng chung giữa màn "Sơ đồ ghế" và màn "Báo ghế hư" nên chọn ở màn
///   ngoài sẽ hiện sẵn ở màn trong và ngược lại.
/// - [reported]: các ghế đã được gửi báo hư (màu cam "Trục trặc").
///
/// TODO: [CS-MERGE] Thay bằng dữ liệu thật từ server khi có API sự cố.
abstract final class SeatReportStore {
  static final ValueNotifier<Set<String>> selected =
      ValueNotifier<Set<String>>(<String>{});

  static final ValueNotifier<Set<String>> reported =
      ValueNotifier<Set<String>>(<String>{});

  static void toggle(String seat) {
    final next = Set<String>.of(selected.value);
    if (!next.remove(seat)) next.add(seat);
    selected.value = next;
  }

  static void clearSelection() {
    selected.value = <String>{};
  }

  /// Chuyển các ghế đang chọn sang trạng thái "đã báo hư".
  static void submit(Iterable<String> seats) {
    reported.value = {...reported.value, ...seats};
    selected.value = <String>{};
  }

  /// Sắp xếp ghế theo hàng rồi số (A1, A2, ..., B1...).
  static List<String> sorted(Iterable<String> seats) {
    final list = seats.toList();
    list.sort((a, b) {
      final rowCompare = a[0].compareTo(b[0]);
      if (rowCompare != 0) return rowCompare;
      final na = int.tryParse(a.substring(1)) ?? 0;
      final nb = int.tryParse(b.substring(1)) ?? 0;
      return na.compareTo(nb);
    });
    return list;
  }
}

