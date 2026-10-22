import 'package:flutter/material.dart';

import 'package:mobile_app/core/database/hive_service.dart';
import 'package:mobile_app/core/utils/time_format.dart';
import 'package:mobile_app/core/models/scan_models.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
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

  String get _roomDisplayName {
    final clean = widget.roomId.replaceAll('seats_config_', '');
    final num = clean.replaceAll('room', '');
    return num.isNotEmpty ? 'Phòng chiếu $num' : widget.roomId;
  }

  void _confirmClearHistory() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: CSAppColors.surface,
        title: const Text('Làm trống lịch sử quét vé?'),
        content: const Text(
          'Thao tác này sẽ xóa toàn bộ danh sách vé đã quét trên máy để bắt đầu phiên kiểm thử mới.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Hủy', style: TextStyle(color: CSAppColors.muted)),
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
      body: SafeArea(
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Lịch sử quét vé',
              subtitle: '${movie.room} · ${movie.time.isNotEmpty ? "Suất ${movie.time}" : "Tất cả suất"}',
              trailingIcon: Icons.delete_sweep_outlined,
              onTrailing: _confirmClearHistory,
            ),
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
                          style: const TextStyle(fontWeight: FontWeight.w700),
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
                    const Text(
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
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
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
                        style: const TextStyle(color: CSAppColors.muted),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
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
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      Text(
                                        'Thời gian: ${formatScanTime(record.scannedAt)}',
                                        style: const TextStyle(
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
