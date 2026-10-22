import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';

class CSSeatMap extends StatelessWidget {
  final bool showWarnings;
  final bool selectionMode;
  final List<String> ignoredSeats;
  final List<String> occupiedSeats;
  final List<String> warningSeats;
  final List<String> brokenSeats;
  final Set<String> selectedSeats;
  final Set<String> reportedSeats;
  final Function(String)? onSeatTapped;

  const CSSeatMap({
    super.key,
    this.showWarnings = false,
    this.selectionMode = false,
    this.ignoredSeats = const [],
    this.occupiedSeats = const [],
    this.warningSeats = const [],
    this.brokenSeats = const [],
    this.selectedSeats = const {},
    this.reportedSeats = const {},
    this.onSeatTapped,
  });

  static String _normalize(String code) {
    final m = RegExp(r'^([a-zA-Z]+)\s*0*(\d+)$').firstMatch(code.trim());
    if (m != null) {
      return '${m.group(1)!.toUpperCase()}${int.parse(m.group(2)!)}';
    }
    return code.trim().toUpperCase();
  }

  bool _hasSeat(Iterable<String> list, String seat) {
    final target = _normalize(seat);
    for (final s in list) {
      if (_normalize(s) == target) return true;
    }
    return false;
  }

  Color _seatColor(String seat) {
    if (_hasSeat(ignoredSeats, seat)) {
      if (_hasSeat(occupiedSeats, seat) || _hasSeat(warningSeats, seat)) {
        return CSAppColors.primary;
      }
      return CSAppColors.surfaceStrong;
    }

    if (selectionMode && _hasSeat(selectedSeats, seat)) {
      return CSAppColors.warning;
    }

    if (showWarnings && _hasSeat(warningSeats, seat)) {
      return CSAppColors.danger;
    }

    if (showWarnings && _hasSeat(brokenSeats, seat)) {
      return CSAppColors.warning;
    }

    if (_hasSeat(reportedSeats, seat)) {
      return CSAppColors.warning;
    }

    if (_hasSeat(occupiedSeats, seat)) {
      return CSAppColors.primary;
    }

    return CSAppColors.surfaceStrong;
  }

  static const Map<String, int> rowSeatCounts = {
    'A': 8,
    'B': 11,
    'C': 11,
    'D': 11,
    'E': 11,
    'F': 11,
    'G': 11,
    'H': 11,
    'I': 11,
    'J': 11,
    'K': 13,
    'L': 16,
  };

  Widget _buildSeatTile(String seat) {
    final isSelected = selectionMode && _hasSeat(selectedSeats, seat);
    return GestureDetector(
      onTap: selectionMode ? () => onSeatTapped?.call(seat) : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: 28,
        height: 24,
        margin: const EdgeInsets.symmetric(horizontal: 1.5),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: _seatColor(seat),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: isSelected ? Colors.white : CSAppColors.border,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Text(
          seat,
          style: const TextStyle(
            fontSize: 8,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  Widget _buildRow(String row, double slotW) {
    const labelW = 20.0;

    if (row == 'A') {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2.5),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'A',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            SizedBox(width: slotW), // Col 1 (spacer for L1)
            SizedBox(width: slotW), // Col 2 (spacer for seat 1)
            for (int i = 1; i <= 8; i++) _buildSeatTile('A$i'), // Cols 3-10
            SizedBox(width: slotW * 6), // Cols 11-16
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'A',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    if (row == 'K') {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2.5),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'K',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            SizedBox(width: slotW), // Col 1 (spacer for L1)
            for (int i = 1; i <= 11; i++) _buildSeatTile('K$i'), // Cols 2-12
            SizedBox(
              width: slotW * 2,
            ), // Cols 13-14 (ô trống thẳng hàng L13, L14 - BỎ LỐI ĐI)
            _buildSeatTile('K12'), // Col 15
            _buildSeatTile('K13'), // Col 16
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'K',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    if (row == 'L') {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2.5),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'L',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            // 16 ghế liền mạch, không có khoảng cách thừa giữa L12 và L13
            for (int i = 1; i <= 16; i++) _buildSeatTile('L$i'),
            const SizedBox(
              width: labelW,
              child: Center(
                child: Text(
                  'L',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Các hàng từ B đến J: 11 ghế mỗi hàng
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: labelW,
            child: Center(
              child: Text(
                row,
                style: const TextStyle(
                  color: CSAppColors.muted,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          SizedBox(width: slotW), // Col 1 (spacer for L1)
          for (int i = 1; i <= 11; i++) _buildSeatTile('$row$i'), // Cols 2-12
          SizedBox(width: slotW * 4), // Cols 13-16 (spacers)
          SizedBox(
            width: labelW,
            child: Center(
              child: Text(
                row,
                style: const TextStyle(
                  color: CSAppColors.muted,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
    const seatW = 28.0;
    const seatMargin = 1.5;
    const slotW = seatW + (seatMargin * 2); // 31.0
    const totalRowWidth = (20.0 * 2) + (slotW * 16); // 536.0

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
          'MÀN HÌNH / SCREEN (136 GHẾ CHUẨN CAMERA)',
          style: TextStyle(
            color: CSAppColors.muted,
            fontSize: 9,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 14),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Column(
            children: [
              // Thanh Lối vào & Lối ra chuẩn theo sơ đồ camera
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: SizedBox(
                  width: totalRowWidth,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: const [
                          Icon(
                            Icons.subdirectory_arrow_right,
                            size: 15,
                            color: CSAppColors.primary,
                          ),
                          SizedBox(width: 4),
                          Text(
                            'LỐI VÀO',
                            style: TextStyle(
                              color: CSAppColors.primary,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: const [
                          Text(
                            'LỐI RA',
                            style: TextStyle(
                              color: CSAppColors.muted,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(width: 4),
                          Icon(
                            Icons.north_east,
                            size: 15,
                            color: CSAppColors.muted,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              ...rows.map((row) => _buildRow(row, slotW)),
            ],
          ),
        ),
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
