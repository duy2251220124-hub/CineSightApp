import 'package:flutter/material.dart';

import 'package:mobile_app/core/database/hive_service.dart';
import 'package:mobile_app/core/utils/time_format.dart';
import 'package:mobile_app/core/models/scan_models.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import '../../../core/utils/room_utils.dart';
import '../../../core/network/api_client.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';

/// Lịch sử quét vé — đọc dữ liệu THẬT từ Hive (scan_history_box).
class CSScanHistoryScreen extends StatefulWidget {
  final String roomId;
  final String showId;

  const CSScanHistoryScreen({super.key, this.roomId = '', this.showId = ''});

  @override
  State<CSScanHistoryScreen> createState() => _CSScanHistoryScreenState();
}

class _CSScanHistoryScreenState extends State<CSScanHistoryScreen> {
  String _query = '';
  bool _isSyncing = false;

  Future<void> _handleManualSync() async {
    final pendingCount = HiveService.getPendingTicketsCount();
    if (pendingCount == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Không có vé tồn đọng nào cần đồng bộ!'),
          backgroundColor: CSAppColors.primary,
        ),
      );
      return;
    }

    setState(() => _isSyncing = true);
    try {
      final success = await ApiClient.syncTicketsToServer(widget.roomId, widget.showId);
      final remaining = HiveService.getPendingTicketsCount();
      if (!mounted) return;

      if (success && remaining == 0) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Đã đồng bộ thành công $pendingCount vé lên máy chủ!'),
            backgroundColor: CSAppColors.success,
          ),
        );
      } else if (remaining < pendingCount) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Đã đồng bộ được ${pendingCount - remaining} vé. Còn lại $remaining vé chờ.'),
            backgroundColor: Colors.orange.shade800,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(ApiClient.lastLoginError ?? 'Không thể gửi vé lên máy chủ. Vui lòng kiểm tra mạng hoặc Server URL!'),
            backgroundColor: CSAppColors.danger,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi đồng bộ: $e'),
            backgroundColor: CSAppColors.danger,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSyncing = false);
      }
    }
  }

  String get _roomDisplayName => formatRoomName(widget.roomId);

  void _confirmClearHistory() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: CSAppColors.surface,
        title: Text(
          'Làm trống lịch sử quét vé?',
          style: TextStyle(color: CSAppColors.textPrimary),
        ),
        content: Text(
          'Thao tác này sẽ xóa toàn bộ danh sách vé đã quét trên máy để bắt đầu phiên kiểm thử mới.',
          style: TextStyle(color: CSAppColors.muted),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('Hủy', style: TextStyle(color: CSAppColors.muted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: CSAppColors.danger,
              foregroundColor: Colors.white,
            ),
            onPressed: () async {
              Navigator.pop(ctx);
              await HiveService.clearAllHistory();
              if (mounted) {
                setState(() {});
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Đã làm trống toàn bộ lịch sử vé trên máy'),
                    backgroundColor: CSAppColors.success,
                  ),
                );
              }
            },
            child: const Text('Xác nhận xóa'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isLight = CSAppColors.isLight;
    final movie = CSMockMovie(
      id: '1',
      title: 'Soát vé rạp',
      time: widget.showId.contains('T') ? widget.showId.split('T')[1] : widget.showId,
      room: _roomDisplayName,
      roomId: widget.roomId,
      showId: widget.showId,
      capacity: 136,
    );

    final all = HiveService.getScanHistory(
      roomId: widget.roomId,
      showId: widget.showId,
    );
    final q = _query.trim().toLowerCase();
    final records = q.isEmpty
        ? all
        : all
            .where(
              (r) =>
                  r.ticket.toLowerCase().contains(q) ||
                  r.seat.toLowerCase().contains(q),
            )
            .toList();

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Lịch sử quét vé',
              subtitle: '${movie.room} · ${movie.time.isNotEmpty ? "Suất ${movie.time}" : "Tất cả suất"}',
              trailingIcon: Icons.delete_sweep_outlined,
              onTrailing: _confirmClearHistory,
            ),
            // Khối trạng thái đồng bộ vé tồn
            Builder(builder: (context) {
              final pendingCount = HiveService.getPendingTicketsCount();
              final Color cardBg = pendingCount > 0
                  ? (isLight ? const Color(0xFFFEF9C3) : const Color(0xFF2E2215))
                  : (isLight ? const Color(0xFFDCFCE7) : const Color(0xFF14241B));
              final Color titleColor = pendingCount > 0
                  ? (isLight ? const Color(0xFFA16207) : const Color(0xFFFEF08A))
                  : (isLight ? const Color(0xFF15803D) : const Color(0xFF86EFAC));
              final Color iconColor = pendingCount > 0
                  ? (isLight ? const Color(0xFFD97706) : const Color(0xFFEAB308))
                  : (isLight ? const Color(0xFF16A34A) : const Color(0xFF22C55E));

              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: iconColor.withValues(alpha: 0.45),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        pendingCount > 0 ? Icons.cloud_off_outlined : Icons.cloud_done_outlined,
                        color: iconColor,
                        size: 22,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              pendingCount > 0
                                  ? 'Có $pendingCount vé lưu offline chưa gửi máy chủ'
                                  : 'Toàn bộ vé đã được đồng bộ với máy chủ',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w600,
                                color: titleColor,
                              ),
                            ),
                            Text(
                              pendingCount > 0
                                  ? 'Bấm nút bên cạnh để gửi ngay khi có mạng'
                                  : 'Dữ liệu đã khớp với máy chủ thời gian thực',
                              style: TextStyle(fontSize: 11, color: CSAppColors.muted),
                            ),
                          ],
                        ),
                      ),
                      if (pendingCount > 0)
                        _isSyncing
                            ? const SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFFEAB308),
                                  foregroundColor: Colors.black,
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  minimumSize: Size.zero,
                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                ),
                                onPressed: _handleManualSync,
                                icon: const Icon(Icons.sync, size: 14),
                                label: const Text(
                                  'Đồng bộ ngay',
                                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                                ),
                              ),
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 6),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: CSAppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          movie.room,
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: CSAppColors.textPrimary,
                          ),
                        ),
                        Text(
                          'Đã soát: ${all.length}/${movie.capacity}',
                          style: TextStyle(
                            color: all.isNotEmpty ? CSAppColors.success : CSAppColors.muted,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Nhấn biểu tượng thùng rác góc trên để làm trống dữ liệu kiểm thử bất cứ lúc nào.',
                      style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 10),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: TextField(
                onChanged: (value) => setState(() => _query = value),
                style: TextStyle(color: CSAppColors.textPrimary, fontSize: 13.5),
                decoration: InputDecoration(
                  prefixIcon: Icon(Icons.search, color: CSAppColors.muted),
                  hintText: 'Tìm kiếm mã vé, số ghế...',
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: records.isEmpty
                  ? Center(
                      child: Text(
                        all.isEmpty
                            ? 'Chưa có vé nào được quét (Sơ đồ ghế đang trống)'
                            : 'Không tìm thấy vé phù hợp',
                        style: TextStyle(color: CSAppColors.muted),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
                      itemCount: records.length,
                      itemBuilder: (context, index) {
                        final record = records[index];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: CSAppCard(
                            padding: const EdgeInsets.all(10),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        record.ticket,
                                        style: TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: CSAppColors.textPrimary,
                                        ),
                                      ),
                                      Text(
                                        'Thời gian: ${formatScanTime(record.scannedAt)}',
                                        style: TextStyle(
                                          color: CSAppColors.muted,
                                          fontSize: 10,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                CSStatusTag(
                                  text: 'Ghế ${record.seat}',
                                  color: CSAppColors.primary,
                                ),
                                const SizedBox(width: 6),
                                const CSStatusTag(
                                  text: 'HỢP LỆ',
                                  color: CSAppColors.success,
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
