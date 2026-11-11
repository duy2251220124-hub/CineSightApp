import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'cs_add_incident_screen.dart';

/// Hàm dùng chung để mở khung Dialog chi tiết sự cố khi người dùng nhấn vào bất kỳ sự cố nào
void showIncidentDetailDialog(
  BuildContext context,
  dynamic incident, {
  VoidCallback? onResolved,
}) {
  final bool isResolved = incident['status'] == 'resolved';
  final statusColor = isResolved ? CSAppColors.success : CSAppColors.warning;
  final title = (incident['title'] ?? 'Sự cố phòng chiếu').toString();
  final roomName = formatRoomName(incident['room_id']?.toString());
  final showId = incident['show_id']?.toString() ?? '';
  final hasShow = showId.isNotEmpty && showId != 'null' && showId != 'N/A';

  // Lấy danh sách ghế hỏng (nếu có)
  String seatsText = '';
  final rawSeats = incident['seat_ids'] ?? incident['seat_id'] ?? incident['seats'];
  if (rawSeats is List && rawSeats.isNotEmpty) {
    seatsText = rawSeats.join(', ');
  } else if (rawSeats is String && rawSeats.trim().isNotEmpty && rawSeats.trim() != '[]') {
    seatsText = rawSeats.replaceAll('[', '').replaceAll(']', '').replaceAll('"', '').trim();
  }

  // Phân loại sự cố & mức độ
  final String categoryCode = (incident['category'] ?? 'seat_damage').toString();
  String categoryLabel = 'Ghế hỏng';
  if (categoryCode == 'equipment') categoryLabel = 'Lỗi thiết bị';
  if (categoryCode == 'facility') categoryLabel = 'Vệ sinh / CSVC';
  if (categoryCode == 'other') categoryLabel = 'Sự cố khác';

  final String severityCode = (incident['severity'] ?? 'high').toString();
  String severityLabel = 'Cao (Khẩn cấp)';
  Color severityColor = CSAppColors.danger;
  if (severityCode == 'medium') {
    severityLabel = 'Trung bình';
    severityColor = CSAppColors.warning;
  } else if (severityCode == 'low') {
    severityLabel = 'Thấp';
    severityColor = CSAppColors.primary;
  }

  final reporterName = (incident['reporter_name'] ?? incident['created_by'] ?? 'Nhân viên').toString();
  final shiftLabel = (incident['shift_label'] ?? incident['reporter_shift'] ?? 'Ca trực').toString();

  // Định dạng thời gian báo cáo
  String dateStr = (incident['created_at'] ?? incident['timestamp'] ?? '').toString();
  if (dateStr.isNotEmpty) {
    try {
      final dt = DateTime.parse(dateStr).toLocal();
      dateStr =
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    } catch (_) {}
  }

  // Định dạng thời gian khắc phục
  String resolvedStr = (incident['resolved_at'] ?? '').toString();
  if (resolvedStr.isNotEmpty) {
    try {
      final dt = DateTime.parse(resolvedStr).toLocal();
      resolvedStr =
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    } catch (_) {}
  }
  final resolvedByName = (incident['resolved_by_name'] ?? '').toString();

  final description = (incident['description'] ?? '').toString().trim();
  final rawImagePath = (incident['image_path'] ?? '').toString().trim();
  final imgUrl = rawImagePath.isNotEmpty ? ApiClient.getImageUrl(rawImagePath) : '';

  showDialog(
    context: context,
    builder: (dialogCtx) {
      return Dialog(
        backgroundColor: CSAppColors.surface,
        surfaceTintColor: Colors.transparent,
        insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: CSAppColors.border, width: 1.2),
        ),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header Dialog
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(7),
                      decoration: BoxDecoration(
                        color: statusColor.withValues(alpha: 0.16),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        isResolved ? Icons.verified_outlined : Icons.report_problem_rounded,
                        color: statusColor,
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'CHI TIẾT SỰ CỐ #${incident['id'] ?? ''}',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: CSAppColors.primary,
                              letterSpacing: 0.5,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            categoryLabel,
                            style: TextStyle(
                              fontSize: 11,
                              color: CSAppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    CSStatusTag(
                      text: isResolved ? 'Đã khắc phục' : 'Chờ xử lý',
                      color: statusColor,
                    ),
                    const SizedBox(width: 4),
                    IconButton(
                      visualDensity: VisualDensity.compact,
                      icon: Icon(Icons.close, size: 20, color: CSAppColors.muted),
                      onPressed: () => Navigator.of(dialogCtx).pop(),
                    ),
                  ],
                ),
                const Divider(height: 20),

                // Tiêu đề sự cố & Mức độ
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        title,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: CSAppColors.textPrimary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: severityColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: severityColor.withValues(alpha: 0.45)),
                      ),
                      child: Text(
                        severityLabel,
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: severityColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                // KHUNG NHẤN MẠNH 1: PHÒNG CHIẾU & GHẾ
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: CSAppColors.primary.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: CSAppColors.primary.withValues(alpha: 0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.meeting_room_rounded, color: CSAppColors.primary, size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'PHÒNG CHIẾU & VỊ TRÍ',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: CSAppColors.primary,
                                letterSpacing: 0.4,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Wrap(
                              spacing: 8,
                              runSpacing: 4,
                              crossAxisAlignment: WrapCrossAlignment.center,
                              children: [
                                Text(
                                  roomName,
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w800,
                                    color: CSAppColors.textPrimary,
                                  ),
                                ),
                                if (seatsText.isNotEmpty)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: CSAppColors.danger.withValues(alpha: 0.18),
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: CSAppColors.danger.withValues(alpha: 0.6)),
                                    ),
                                    child: Text(
                                      'Ghế: $seatsText',
                                      style: const TextStyle(
                                        fontSize: 12.5,
                                        fontWeight: FontWeight.w800,
                                        color: CSAppColors.danger,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                            if (hasShow) ...[
                              const SizedBox(height: 3),
                              Text(
                                'Suất chiếu: $showId',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: CSAppColors.textSecondary,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),

                // KHUNG NHẤN MẠNH 2: NGƯỜI BÁO CÁO & CA TRỰC
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: CSAppColors.surfaceStrong,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: CSAppColors.border),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.person_pin_rounded, color: CSAppColors.success, size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'NGƯỜI BÁO CÁO & CA TRỰC',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: CSAppColors.success,
                                letterSpacing: 0.4,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              reporterName,
                              style: TextStyle(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w800,
                                color: CSAppColors.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              shiftLabel,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: CSAppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),

                // KHUNG NHẤN MẠNH 3: GIỜ BÁO CÁO
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: CSAppColors.warning.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: CSAppColors.warning.withValues(alpha: 0.45)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.access_time_filled_rounded, color: CSAppColors.warning, size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'THỜI GIAN BÁO CÁO',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: CSAppColors.warning,
                                letterSpacing: 0.4,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              dateStr.isNotEmpty ? dateStr : 'Không rõ thời gian',
                              style: TextStyle(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w800,
                                color: CSAppColors.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // Mô tả chi tiết
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    'NỘI DUNG GHI CHÚ / BÀN GIAO',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: CSAppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(11),
                    decoration: BoxDecoration(
                      color: CSAppColors.surfaceStrong,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: CSAppColors.border),
                    ),
                    child: Text(
                      description,
                      style: TextStyle(
                        fontSize: 13,
                        color: CSAppColors.textPrimary,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],

                // Ảnh chụp hiện trường
                if (imgUrl.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text(
                    'ẢNH CHỤP HIỆN TRƯỜNG (CHẠM ĐỂ PHÓNG TO)',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      color: CSAppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: InkWell(
                      onTap: () {
                        showDialog(
                          context: dialogCtx,
                          builder: (zoomCtx) => Dialog(
                            backgroundColor: Colors.transparent,
                            insetPadding: const EdgeInsets.all(12),
                            child: Stack(
                              alignment: Alignment.topRight,
                              children: [
                                InteractiveViewer(
                                  child: Image.network(
                                    imgUrl,
                                    headers: const {'ngrok-skip-browser-warning': 'true'},
                                    fit: BoxFit.contain,
                                  ),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.close, color: Colors.white, size: 28),
                                  onPressed: () => Navigator.of(zoomCtx).pop(),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                      child: Stack(
                        alignment: Alignment.bottomRight,
                        children: [
                          Image.network(
                            imgUrl,
                            height: 180,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            headers: const {'ngrok-skip-browser-warning': 'true'},
                            errorBuilder: (context, error, stackTrace) => Container(
                              height: 90,
                              color: CSAppColors.surfaceStrong,
                              alignment: Alignment.center,
                              child: Text(
                                'Không tải được ảnh hiện trường',
                                style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                              ),
                            ),
                          ),
                          Container(
                            margin: const EdgeInsets.all(8),
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.78),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.zoom_out_map, size: 14, color: Colors.white),
                                SizedBox(width: 5),
                                Text(
                                  'Phóng to ảnh',
                                  style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],

                // Thông tin khắc phục (nếu đã xử lý)
                if (isResolved && resolvedStr.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: CSAppColors.success.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: CSAppColors.success.withValues(alpha: 0.4)),
                    ),
                    child: Text(
                      'Đã khắc phục lúc: $resolvedStr${resolvedByName.isNotEmpty ? ' · Bởi: $resolvedByName' : ''}',
                      style: const TextStyle(
                        color: CSAppColors.success,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],

                const SizedBox(height: 16),
                // Nút hành động
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.of(dialogCtx).pop(),
                      child: const Text('Đóng'),
                    ),
                    if (!isResolved && onResolved != null) ...[
                      const SizedBox(width: 8),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: CSAppColors.success,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        ),
                        onPressed: () async {
                          final res = await ApiClient.resolveIncident(incident['id']);
                          if (!dialogCtx.mounted) return;
                          Navigator.of(dialogCtx).pop();
                          if (res['success'] == true) {
                            onResolved();
                          } else if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text(res['error'] ?? 'Lỗi xử lý sự cố')),
                            );
                          }
                        },
                        icon: const Icon(Icons.check_circle_outline, size: 17),
                        label: const Text(
                          'Đánh dấu đã xử lý',
                          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ),
      );
    },
  );
}

class CSHandoverScreen extends StatefulWidget {
  const CSHandoverScreen({super.key});

  @override
  State<CSHandoverScreen> createState() => _CSHandoverScreenState();
}

class _CSHandoverScreenState extends State<CSHandoverScreen> {
  List<dynamic> _incidents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadIncidents();
  }

  Future<void> _loadIncidents() async {
    final incidents = await ApiClient.getIncidents();
    if (mounted) {
      setState(() {
        _incidents = incidents;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final pending = _incidents.where((item) => item['status'] == 'open').toList();
    final resolved = _incidents.where((item) => item['status'] == 'resolved').toList();

    return Scaffold(
      backgroundColor: CSAppColors.background,
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 78),
        child: FloatingActionButton(
          backgroundColor: CSAppColors.primary,
          foregroundColor: Colors.white,
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (addCtx) => CSAddIncidentScreen(
                  reportedSeats: const [],
                  onIncidentAdded: () {
                    _loadIncidents();
                    Navigator.pop(addCtx);
                  },
                ),
              ),
            );
          },
          child: const Icon(Icons.add),
        ),
      ),
      body: SafeArea(
        bottom: false,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
                children: [
                  const CSScreenHeader(
                    title: 'Sự cố & Bàn giao',
                    subtitle: 'Chạm vào từng sự cố để mở khung xem chi tiết',
                    showBack: true,
                  ),
                  Text(
                    'ĐANG CHỜ XỬ LÝ (${pending.length})',
                    style: const TextStyle(
                      color: CSAppColors.warning,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ...pending.map(
                    (incident) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: CSIncidentCard(
                        incident: incident,
                        onResolved: _loadIncidents,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'ĐÃ KHẮC PHỤC TRONG CA (${resolved.length})',
                              style: const TextStyle(
                                color: CSAppColors.success,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Tự động làm sạch sau 1 tiếng kể từ lúc giải quyết',
                              style: TextStyle(color: CSAppColors.muted, fontSize: 10),
                            ),
                          ],
                        ),
                      ),
                      if (resolved.isNotEmpty)
                        TextButton.icon(
                          style: TextButton.styleFrom(
                            foregroundColor: CSAppColors.danger,
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          ),
                          onPressed: () async {
                            final confirmed = await showDialog<bool>(
                              context: context,
                              builder: (ctx) => AlertDialog(
                                backgroundColor: CSAppColors.surface,
                                title: Text(
                                  'Dọn sạch sự cố đã xử lý?',
                                  style: TextStyle(fontSize: 15, color: CSAppColors.textPrimary),
                                ),
                                content: Text(
                                  'Toàn bộ các sự cố đã khắc phục sẽ được xóa ngay lập tức khỏi hệ thống.',
                                  style: TextStyle(fontSize: 13, color: CSAppColors.muted),
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: () => Navigator.pop(ctx, false),
                                    child: const Text('Hủy'),
                                  ),
                                  ElevatedButton(
                                    style: ElevatedButton.styleFrom(backgroundColor: CSAppColors.danger),
                                    onPressed: () => Navigator.pop(ctx, true),
                                    child: const Text('Xóa tất cả', style: TextStyle(color: Colors.white)),
                                  ),
                                ],
                              ),
                            );
                            if (confirmed == true) {
                              await ApiClient.clearResolvedIncidents();
                              _loadIncidents();
                            }
                          },
                          icon: const Icon(Icons.delete_sweep_outlined, size: 16),
                          label: const Text('Dọn sạch', style: TextStyle(fontSize: 11)),
                        ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ...resolved.map(
                    (incident) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: CSIncidentCard(
                        incident: incident,
                        onResolved: _loadIncidents,
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

class CSIncidentCard extends StatelessWidget {
  final dynamic incident;
  final VoidCallback onResolved;

  const CSIncidentCard({
    super.key,
    required this.incident,
    required this.onResolved,
  });

  @override
  Widget build(BuildContext context) {
    final bool isResolved = incident['status'] == 'resolved';
    final color = isResolved ? CSAppColors.success : CSAppColors.warning;
    final title = incident['title'] ?? 'Sự cố';
    final roomName = formatRoomName(incident['room_id']?.toString());
    final reporterName = incident['reporter_name'] ?? 'Ẩn danh';
    final shiftLabel = incident['shift_label'] ?? 'Ca trực';

    // Format date string from ISO
    String dateStr = incident['created_at'] ?? '';
    if (dateStr.isNotEmpty) {
      try {
        final dt = DateTime.parse(dateStr).toLocal();
        dateStr =
            '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      } catch (_) {}
    }

    String resolvedStr = incident['resolved_at'] ?? '';
    if (resolvedStr.isNotEmpty) {
      try {
        final dt = DateTime.parse(resolvedStr).toLocal();
        resolvedStr =
            '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
      } catch (_) {}
    }

    return CSAppCard(
      onTap: () => showIncidentDetailDialog(
        context,
        incident,
        onResolved: onResolved,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Hàng tiêu đề + Trạng thái
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    color: CSAppColors.textPrimary,
                  ),
                ),
              ),
              CSStatusTag(
                text: isResolved ? 'Đã khắc phục' : 'Chờ xử lý',
                color: color,
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Nhấn mạnh Phòng chiếu, Người báo và Giờ báo bằng khung thông tin nổi bật
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: CSAppColors.surfaceStrong,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: CSAppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Phòng chiếu nổi bật
                Row(
                  children: [
                    const Icon(Icons.meeting_room_rounded, size: 16, color: CSAppColors.primary),
                    const SizedBox(width: 6),
                    Text(
                      'Phòng: ',
                      style: TextStyle(color: CSAppColors.muted, fontSize: 12.5, fontWeight: FontWeight.w600),
                    ),
                    Expanded(
                      child: Text(
                        roomName,
                        style: TextStyle(
                          color: CSAppColors.textPrimary,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),

                // 2. Người báo cáo & Ca trực nổi bật
                Row(
                  children: [
                    const Icon(Icons.person_pin_rounded, size: 16, color: CSAppColors.success),
                    const SizedBox(width: 6),
                    Text(
                      'Người báo: ',
                      style: TextStyle(color: CSAppColors.muted, fontSize: 12.5, fontWeight: FontWeight.w600),
                    ),
                    Expanded(
                      child: Text(
                        '$reporterName ($shiftLabel)',
                        style: TextStyle(
                          color: CSAppColors.textPrimary,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),

                // 3. Giờ báo cáo nổi bật
                if (dateStr.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.access_time_filled_rounded, size: 16, color: CSAppColors.warning),
                      const SizedBox(width: 6),
                      Text(
                        'Giờ báo: ',
                        style: TextStyle(color: CSAppColors.muted, fontSize: 12.5, fontWeight: FontWeight.w600),
                      ),
                      Expanded(
                        child: Text(
                          dateStr,
                          style: const TextStyle(
                            color: CSAppColors.warning,
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),

          if (incident['description'] != null && incident['description'].toString().trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              incident['description'].toString(),
              style: TextStyle(fontSize: 12.5, color: CSAppColors.textSecondary),
            ),
          ],
          if (incident['image_path'] != null && incident['image_path'].toString().trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            Builder(
              builder: (ctx) {
                final imgUrl = ApiClient.getImageUrl(incident['image_path']?.toString());
                return ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: InkWell(
                    onTap: () {
                      showDialog(
                        context: ctx,
                        builder: (dialogCtx) => Dialog(
                          backgroundColor: Colors.transparent,
                          insetPadding: const EdgeInsets.all(12),
                          child: Stack(
                            alignment: Alignment.topRight,
                            children: [
                              InteractiveViewer(
                                child: Image.network(
                                  imgUrl,
                                  headers: const {'ngrok-skip-browser-warning': 'true'},
                                  fit: BoxFit.contain,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, color: Colors.white, size: 28),
                                onPressed: () => Navigator.of(dialogCtx).pop(),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                    child: Stack(
                      alignment: Alignment.bottomRight,
                      children: [
                        Image.network(
                          imgUrl,
                          height: 140,
                          width: double.infinity,
                          fit: BoxFit.cover,
                          headers: const {'ngrok-skip-browser-warning': 'true'},
                          errorBuilder: (context, error, stackTrace) => Container(
                            height: 80,
                            color: CSAppColors.surfaceStrong,
                            alignment: Alignment.center,
                            child: Text(
                              'Không tải được ảnh hiện trường',
                              style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                            ),
                          ),
                        ),
                        Container(
                          margin: const EdgeInsets.all(6),
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.75),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.zoom_in, size: 14, color: Colors.white),
                              SizedBox(width: 4),
                              Text('Xem ảnh', style: TextStyle(color: Colors.white, fontSize: 10)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
          if (isResolved && resolvedStr.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                'Khắc phục lúc: $resolvedStr (Tự xóa sau 1h)',
                style: const TextStyle(
                  color: CSAppColors.success,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.touch_app_outlined, size: 13, color: CSAppColors.primary),
              const SizedBox(width: 4),
              const Expanded(
                child: Text(
                  'Chạm vào thẻ để mở chi tiết sự cố',
                  style: TextStyle(
                    fontSize: 11,
                    color: CSAppColors.primary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              if (!isResolved) ...[
                TextButton(
                  onPressed: () async {
                    final res = await ApiClient.resolveIncident(incident['id']);
                    if (res['success'] == true) {
                      onResolved();
                    } else {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(res['error'] ?? 'Lỗi')),
                        );
                      }
                    }
                  },
                  child: const Text('Đánh dấu đã xử lý'),
                ),
                const SizedBox(width: 4),
              ],
              TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: isResolved ? CSAppColors.danger : CSAppColors.muted,
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                ),
                onPressed: () async {
                  final confirmed = await showDialog<bool>(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      backgroundColor: CSAppColors.surface,
                      title: Text(
                        'Xóa sự cố này?',
                        style: TextStyle(fontSize: 15, color: CSAppColors.textPrimary),
                      ),
                      content: Text(
                        'Bạn có chắc chắn muốn xóa sự cố "${incident['title'] ?? 'N/A'}" ngay lập tức?',
                        style: TextStyle(fontSize: 13, color: CSAppColors.muted),
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Hủy'),
                        ),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(backgroundColor: CSAppColors.danger),
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Xóa ngay', style: TextStyle(color: Colors.white)),
                        ),
                      ],
                    ),
                  );
                  if (confirmed == true) {
                    final res = await ApiClient.deleteIncident(incident['id']);
                    if (res['success'] == true) {
                      onResolved();
                    } else {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(res['error'] ?? 'Không thể xóa sự cố')),
                        );
                      }
                    }
                  }
                },
                icon: const Icon(Icons.delete_outline, size: 16),
                label: Text(
                  isResolved ? 'Xóa sự cố ngay' : 'Xóa',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
