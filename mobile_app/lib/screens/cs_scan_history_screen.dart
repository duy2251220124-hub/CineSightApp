import 'package:flutter/material.dart';

import '../core/database/hive_service.dart';
import '../core/utils/time_format.dart';
import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_status_tag.dart';

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

  @override
  Widget build(BuildContext context) {
    final movie = CSMockData.movies.firstWhere(
      (m) => m.roomId == widget.roomId,
      orElse: () => CSMockData.movies.first,
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
              subtitle: '${movie.title} · ${movie.room}',
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: CSAppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${movie.date} · ${movie.time}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      'Tổng số vé đã quét: ${all.length}/${movie.capacity}',
                      style: const TextStyle(color: CSAppColors.muted),
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
                            ? 'Chưa có vé nào được quét cho suất này'
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
