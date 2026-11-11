import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';

class CSSeatMap extends StatelessWidget {
  final String roomId;
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
    this.roomId = 'room1',
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

  bool _isEmptySeat(String seat) {
    if (_hasSeat(ignoredSeats, seat)) {
      return !(_hasSeat(occupiedSeats, seat) || _hasSeat(warningSeats, seat));
    }
    if (selectionMode && _hasSeat(selectedSeats, seat)) return false;
    if (_hasSeat(brokenSeats, seat) || _hasSeat(reportedSeats, seat)) {
      return false;
    }
    if (showWarnings && _hasSeat(warningSeats, seat)) return false;
    if (_hasSeat(occupiedSeats, seat)) return false;
    return true;
  }

  Color _seatColor(String seat) {
    if (_hasSeat(ignoredSeats, seat)) {
      if (_hasSeat(occupiedSeats, seat) || _hasSeat(warningSeats, seat)) {
        return CSAppColors.primary;
      }
      return CSAppColors.seatEmpty;
    }

    if (selectionMode && _hasSeat(selectedSeats, seat)) {
      return CSAppColors.warning;
    }

    // Ghế hỏng / sự cố luôn hiển thị màu cam
    if (_hasSeat(brokenSeats, seat) || _hasSeat(reportedSeats, seat)) {
      return CSAppColors.warning;
    }

    // Ghế cảnh báo AI
    if (showWarnings && _hasSeat(warningSeats, seat)) {
      return CSAppColors.danger;
    }

    // Ghế đã soát vé hợp lệ
    if (_hasSeat(occupiedSeats, seat)) {
      return CSAppColors.primary;
    }

    return CSAppColors.seatEmpty;
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
    final isEmpty = _isEmptySeat(seat);
    return GestureDetector(
      onTap: onSeatTapped != null ? () => onSeatTapped!(seat) : null,
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
            color: isSelected ? CSAppColors.primary : CSAppColors.border,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Text(
          seat,
          style: TextStyle(
            fontSize: 8,
            fontWeight: FontWeight.bold,
            color: isEmpty ? CSAppColors.seatEmptyText : Colors.white,
          ),
        ),
      ),
    );
  }

  Widget _buildRowLabel(String row) {
    return SizedBox(
      width: 20.0,
      child: Center(
        child: Text(
          row,
          style: TextStyle(
            color: CSAppColors.muted,
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildRow(String row, double slotW) {
    if (row == 'A') {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 2.5),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildRowLabel('A'),
            SizedBox(width: slotW), // Col 1 (spacer for L1)
            SizedBox(width: slotW), // Col 2 (spacer for seat 1)
            for (int i = 8; i >= 1; i--) _buildSeatTile('A$i'), // Cols 3-10
            SizedBox(width: slotW * 6), // Cols 11-16
            _buildRowLabel('A'),
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
            _buildRowLabel('K'),
            SizedBox(width: slotW), // Col 1 (spacer for L1)
            for (int i = 13; i >= 3; i--) _buildSeatTile('K$i'), // Cols 2-12
            SizedBox(
              width: slotW * 2,
            ), // Cols 13-14 (ô trống thẳng hàng L4, L3 - BỎ LỐI ĐI)
            _buildSeatTile('K2'), // Col 15
            _buildSeatTile('K1'), // Col 16
            _buildRowLabel('K'),
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
            _buildRowLabel('L'),
            for (int i = 16; i >= 1; i--) _buildSeatTile('L$i'),
            _buildRowLabel('L'),
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
          _buildRowLabel(row),
          SizedBox(width: slotW), // Col 1 (spacer for L1)
          for (int i = 11; i >= 1; i--) _buildSeatTile('$row$i'), // Cols 2-12
          SizedBox(width: slotW * 4), // Cols 13-16 (spacers)
          _buildRowLabel(row),
        ],
      ),
    );
  }

  Widget _buildRoom3Row(String row, double slotW) {
    final int count = (row == 'A') ? 10 : ((row == 'J') ? 18 : 13);
    final int leftSpacers = (row == 'A') ? 4 : ((row == 'J') ? 0 : 2);
    final int rightSpacers = (row == 'A') ? 4 : ((row == 'J') ? 0 : 3);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.5),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildRowLabel(row),
          if (leftSpacers > 0) SizedBox(width: slotW * leftSpacers),
          for (int i = 1; i <= count; i++) _buildSeatTile('$row$i'),
          if (rightSpacers > 0) SizedBox(width: slotW * rightSpacers),
          _buildRowLabel(row),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isRoom3 =
        roomId.toLowerCase().contains('room3') || roomId.contains('3');
    final rows = isRoom3
        ? ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        : ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'];
    const seatW = 28.0;
    const seatMargin = 1.5;
    const slotW = seatW + (seatMargin * 2); // 31.0
    final totalRowWidth = (20.0 * 2) + (slotW * (isRoom3 ? 18 : 16));

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
        Text(
          'MÀN HÌNH CHIẾU / SCREEN',
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
                      const Row(
                        children: [
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
                        children: [
                          Text(
                            'LỐI RA',
                            style: TextStyle(
                              color: CSAppColors.muted,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 4),
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
              ...rows.map(
                (row) => isRoom3
                    ? _buildRoom3Row(row, slotW)
                    : _buildRow(row, slotW),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),
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
          style: TextStyle(color: CSAppColors.muted, fontSize: 10),
        ),
      ],
    );
  }
}
