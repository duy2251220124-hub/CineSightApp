import 'package:flutter/material.dart';

import '../mock/mock_data.dart';
import '../mock/seat_report_store.dart';
import '../theme/app_theme.dart';

class CSSeatMap extends StatelessWidget {
  /// Bật ở màn "Chi tiết cảnh báo": hiện ghế cảnh báo (đỏ) và ghế trục trặc
  /// mẫu của kịch bản cảnh báo (cam).
  final bool showWarnings;

  /// Bật ở màn "Sơ đồ ghế" / "Báo ghế hư": cho phép chạm để chọn ghế hư.
  /// Lựa chọn được lưu ở [SeatReportStore.selected].
  final bool selectionMode;

  /// Ghế đã được xử lý xong -> trả về màu bình thường.
  final List<String> ignoredSeats;

  const CSSeatMap({
    super.key,
    this.showWarnings = false,
    this.selectionMode = false,
    this.ignoredSeats = const [],
  });

  Color _seatColor(String seat, Set<String> selected, Set<String> reported) {
    if (ignoredSeats.contains(seat)) {
      if (CSMockData.occupiedSeats.contains(seat) ||
          CSMockData.warningSeats.contains(seat)) {
        return CSAppColors.primary;
      }
      return CSAppColors.surfaceStrong;
    }

    if (selectionMode && selected.contains(seat)) {
      return CSAppColors.warning;
    }

    if (showWarnings && CSMockData.warningSeats.contains(seat)) {
      return CSAppColors.danger;
    }

    if (showWarnings && CSMockData.brokenSeats.contains(seat)) {
      return CSAppColors.warning;
    }

    if (reported.contains(seat)) {
      return CSAppColors.warning;
    }

    if (CSMockData.occupiedSeats.contains(seat)) {
      return CSAppColors.primary;
    }

    return CSAppColors.surfaceStrong;
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Set<String>>(
      valueListenable: SeatReportStore.reported,
      builder: (context, reported, _) {
        return ValueListenableBuilder<Set<String>>(
          valueListenable: SeatReportStore.selected,
          builder: (context, selected, _) {
            return _buildMap(selected, reported);
          },
        );
      },
    );
  }

  Widget _buildMap(Set<String> selected, Set<String> reported) {
    const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K'];

    return Column(
      children: [
        Container(
          width: 260,
          height: 12,
          decoration: BoxDecoration(
            border: const Border(
              top: BorderSide(color: CSAppColors.primary, width: 2),
            ),
            borderRadius: BorderRadius.circular(50),
          ),
        ),
        const Text(
          'MÀN HÌNH / SCREEN',
          style: TextStyle(color: CSAppColors.muted, fontSize: 9),
        ),
        const SizedBox(height: 16),
        ...rows.map((row) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  width: 16,
                  child: Text(
                    row,
                    style: const TextStyle(
                      color: CSAppColors.muted,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                ...List.generate(8, (index) {
                  final seat = '$row${index + 1}';
                  final isSelected = selectionMode && selected.contains(seat);

                  return GestureDetector(
                    onTap: selectionMode
                        ? () => SeatReportStore.toggle(seat)
                        : null,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      width: 33,
                      height: 27,
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: _seatColor(seat, selected, reported),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: isSelected ? Colors.white : CSAppColors.border,
                          width: isSelected ? 2 : 1,
                        ),
                      ),
                      child: Text(
                        seat,
                        style: const TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  );
                }),
                SizedBox(
                  width: 16,
                  child: Text(
                    row,
                    textAlign: TextAlign.end,
                    style: const TextStyle(
                      color: CSAppColors.muted,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          );
        }),
        const SizedBox(height: 20),
        const Wrap(
          spacing: 16,
          runSpacing: 8,
          alignment: WrapAlignment.center,
          children: [
            CSLegendItem('Trống', CSAppColors.surfaceStrong),
            CSLegendItem('Đã có người', CSAppColors.primary),
            CSLegendItem('Trục trặc', CSAppColors.warning),
            CSLegendItem('Cảnh báo', CSAppColors.danger),
          ],
        ),
      ],
    );
  }
}

class CSLegendItem extends StatelessWidget {
  final String label;
  final Color color;

  const CSLegendItem(this.label, this.color, {super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
            border: Border.all(color: CSAppColors.border),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(color: CSAppColors.muted, fontSize: 10),
        ),
      ],
    );
  }
}
