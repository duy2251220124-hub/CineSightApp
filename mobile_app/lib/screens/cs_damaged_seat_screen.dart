import 'package:flutter/material.dart';

import '../mock/seat_report_store.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_primary_button.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_seat_map.dart';

class CSDamagedSeatScreen extends StatelessWidget {
  /// Gọi khi bấm "Thêm ảnh ghế hư" — truyền danh sách ghế đang chọn.
  final ValueChanged<List<String>>? onAddPhoto;

  const CSDamagedSeatScreen({super.key, this.onAddPhoto});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(horizontal: 10),
                child: Column(
                  children: [
                    CSScreenHeader(
                      title: 'Báo ghế hư - Rạp 5',
                      subtitle: 'Chạm vào ghế để chọn / bỏ chọn',
                    ),
                    CSSeatMap(selectionMode: true),
                    SizedBox(height: 12),
                  ],
                ),
              ),
            ),
            ValueListenableBuilder<Set<String>>(
              valueListenable: SeatReportStore.selected,
              builder: (context, selected, _) {
                final seats = SeatReportStore.sorted(selected);
                final hasSeats = seats.isNotEmpty;

                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: const BoxDecoration(
                    color: CSAppColors.surface,
                    border: Border(top: BorderSide(color: CSAppColors.border)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              hasSeats
                                  ? 'Ghế đã chọn (${seats.length})'
                                  : 'Chưa chọn ghế nào',
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          if (hasSeats)
                            TextButton(
                              onPressed: SeatReportStore.clearSelection,
                              child: const Text('Bỏ chọn tất cả'),
                            ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      if (hasSeats)
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: seats
                              .map(
                                (seat) => InputChip(
                                  label: Text(seat),
                                  labelStyle: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  backgroundColor: CSAppColors.warning
                                      .withValues(alpha: 0.25),
                                  side: const BorderSide(
                                    color: CSAppColors.warning,
                                  ),
                                  deleteIconColor: Colors.white,
                                  onDeleted: () => SeatReportStore.toggle(seat),
                                ),
                              )
                              .toList(),
                        )
                      else
                        const Text(
                          'Chạm vào ghế trên sơ đồ, ghế sẽ chuyển sang màu cam.',
                          style: TextStyle(
                            color: CSAppColors.muted,
                            fontSize: 11,
                          ),
                        ),
                      const SizedBox(height: 10),
                      CSPrimaryButton(
                        label: 'Thêm ảnh ghế hư',
                        icon: Icons.add_a_photo_outlined,
                        onPressed: hasSeats && onAddPhoto != null
                            ? () => onAddPhoto!(seats)
                            : null,
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
