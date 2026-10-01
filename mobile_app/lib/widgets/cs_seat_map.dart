import 'package:flutter/material.dart';
import '../mock/mock_data.dart';
import '../theme/app_theme.dart';

class CSSeatMap extends StatefulWidget {
  final bool showWarnings;
  final bool selectionMode;
  final List<String> ignoredSeats;
  final Function(List<String>)? onSelectionChanged;

  const CSSeatMap({
    super.key,
    this.showWarnings = false,
    this.selectionMode = false,
    this.ignoredSeats = const [],
    this.onSelectionChanged,
  });

  @override
  State<CSSeatMap> createState() => _CSSeatMapState();
}

class _CSSeatMapState extends State<CSSeatMap> {
  final List<String> _selectedSeats = [];

  Color _seatColor(String seat) {
    if (widget.ignoredSeats.contains(seat)) {
      if (CSMockData.occupiedSeats.contains(seat) || CSMockData.warningSeats.contains(seat)) return CSAppColors.primary;
      return CSAppColors.surfaceStrong;
    }

    // In selection mode, tapped seats become WARNING (orange)
    if (widget.selectionMode && _selectedSeats.contains(seat)) {
      return CSAppColors.warning;
    }
    // Also keep previously selected broken seats red/orange if needed, but let's just use warning
    if (widget.selectionMode && CSMockData.selectedBrokenSeats.contains(seat) && !_selectedSeats.contains(seat)) {
      // If it was pre-selected in mock, we can show it as warning too, 
      // but to allow toggle, we just rely on _selectedSeats if we wanted full control.
      // For visual sake, let's keep it.
      return CSAppColors.warning; 
    }

    if (widget.showWarnings && CSMockData.warningSeats.contains(seat)) {
      return CSAppColors.danger;
    }

    if (CSMockData.brokenSeats.contains(seat)) {
      return CSAppColors.warning;
    }

    if (CSMockData.occupiedSeats.contains(seat)) {
      return CSAppColors.primary;
    }

    return CSAppColors.surfaceStrong;
  }

  void _handleTap(String seat) {
    if (!widget.selectionMode) return;
    setState(() {
      if (_selectedSeats.contains(seat)) {
        _selectedSeats.remove(seat);
      } else {
        _selectedSeats.add(seat);
      }
    });
    if (widget.onSelectionChanged != null) {
      widget.onSelectionChanged!(_selectedSeats);
    }
  }

  @override
  Widget build(BuildContext context) {
    const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K'];

    return Column(
      children: [
        Container(
          width: 260,
          height: 12,
          decoration: BoxDecoration(
            border: const Border(
              top: BorderSide(
                color: CSAppColors.primary,
                width: 2,
              ),
            ),
            borderRadius: BorderRadius.circular(50),
          ),
        ),
        const Text(
          'MÀN HÌNH / SCREEN',
          style: TextStyle(
            color: CSAppColors.muted,
            fontSize: 9,
          ),
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
                  
                  return GestureDetector(
                    onTap: () => _handleTap(seat),
                    child: Container(
                      width: 33,
                      height: 27,
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: _seatColor(seat),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: CSAppColors.border),
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
          style: const TextStyle(
            color: CSAppColors.muted,
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}
