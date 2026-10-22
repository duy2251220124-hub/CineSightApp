import os

home_screen_path = 'lib/features/home/presentation/home_screen.dart'
with open(home_screen_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
"""                            builder: (ctx2) => CSSeatMapScreen(
                              onReportDamagedSeat: () {""",
"""                            builder: (ctx2) => CSSeatMapScreen(
                              roomId: _selectedShowtime['roomId'],
                              showId: _selectedShowtime['showId'],
                              onReportDamagedSeat: () {""")

with open(home_screen_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Now rewrite cs_seat_map_screen.dart
seat_map_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/features/rooms/presentation/widgets/cs_seat_map.dart';

class CSSeatMapScreen extends StatefulWidget {
  final String roomId;
  final String showId;
  final VoidCallback? onReportDamagedSeat;

  const CSSeatMapScreen({
    super.key, 
    required this.roomId,
    required this.showId,
    this.onReportDamagedSeat
  });

  @override
  State<CSSeatMapScreen> createState() => _CSSeatMapScreenState();
}

class _CSSeatMapScreenState extends State<CSSeatMapScreen> {
  bool _isLoading = true;
  List<String> _occupiedSeats = [];
  Set<String> _selectedSeats = {};
  Set<String> _reportedSeats = {};

  @override
  void initState() {
    super.initState();
    _loadTickets();
  }

  Future<void> _loadTickets() async {
    final tickets = await ApiClient.fetchTickets(widget.roomId, widget.showId);
    final List<String> occupied = [];
    for (var t in tickets) {
      if (t['seat'] != null) occupied.add(t['seat']);
      if (t['seat_id'] != null) occupied.add(t['seat_id']);
    }
    
    if (mounted) {
      setState(() {
        _occupiedSeats = occupied;
        _isLoading = false;
      });
    }
  }

  void _onSeatTapped(String seat) {
    setState(() {
      if (_selectedSeats.contains(seat)) {
        _selectedSeats.remove(seat);
      } else {
        _selectedSeats.add(seat);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final percentage = _occupiedSeats.isNotEmpty ? 100 : 0; // Tạm tính

    return Scaffold(
      body: SafeArea(
        child: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            CSScreenHeader(
              title: 'Sơ đồ ghế - ${widget.roomId}',
              subtitle: 'Phòng chiếu chuẩn',
              trailingIcon: Icons.settings_outlined,
            ),
            CSAppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Suất chiếu hiện tại',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                  Text(
                    '${widget.showId} | ${widget.roomId}',
                    style: const TextStyle(
                      color: CSAppColors.muted,
                      fontSize: 10,
                    ),
                  ),
                  Row(
                    children: [
                      Text(
                        'Đã bán: ${_occupiedSeats.length}',
                        style: const TextStyle(
                          color: CSAppColors.muted,
                          fontSize: 10,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '$percentage%',
                        style: const TextStyle(
                          color: CSAppColors.primary,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Chạm vào ghế trên sơ đồ để chọn ghế hư',
              textAlign: TextAlign.center,
              style: TextStyle(color: CSAppColors.muted, fontSize: 11),
            ),
            const SizedBox(height: 10),
            CSSeatMap(
              selectionMode: true,
              occupiedSeats: _occupiedSeats,
              selectedSeats: _selectedSeats,
              reportedSeats: _reportedSeats,
              warningSeats: const [],
              brokenSeats: const [],
              ignoredSeats: const [],
              onSeatTapped: _onSeatTapped,
            ),
            const SizedBox(height: 22),
            CSPrimaryButton(
              label: _selectedSeats.isEmpty ? 'Báo ghế hư' : 'Báo ghế hư (${_selectedSeats.length} ghế)',
              icon: Icons.report_problem_outlined,
              onPressed: _selectedSeats.isEmpty ? null : () {
                 setState(() {
                   _reportedSeats.addAll(_selectedSeats);
                   _selectedSeats.clear();
                 });
                 widget.onReportDamagedSeat?.call();
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
"""

with open('lib/features/rooms/presentation/cs_seat_map_screen.dart', 'w', encoding='utf-8') as f:
    f.write(seat_map_screen_content)


# Rewrite cs_seat_map.dart
seat_map_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';

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

  Color _seatColor(String seat) {
    if (ignoredSeats.contains(seat)) {
      if (occupiedSeats.contains(seat) || warningSeats.contains(seat)) {
        return CSAppColors.primary;
      }
      return CSAppColors.surfaceStrong;
    }

    if (selectionMode && selectedSeats.contains(seat)) {
      return CSAppColors.warning;
    }

    if (showWarnings && warningSeats.contains(seat)) {
      return CSAppColors.danger;
    }

    if (showWarnings && brokenSeats.contains(seat)) {
      return CSAppColors.warning;
    }

    if (reportedSeats.contains(seat)) {
      return CSAppColors.warning;
    }

    if (occupiedSeats.contains(seat)) {
      return CSAppColors.primary;
    }

    return CSAppColors.surfaceStrong;
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
                  final isSelected = selectionMode && selectedSeats.contains(seat);

                  return GestureDetector(
                    onTap: selectionMode ? () => onSeatTapped?.call(seat) : null,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      width: 33,
                      height: 27,
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
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
"""

with open('lib/features/rooms/presentation/widgets/cs_seat_map.dart', 'w', encoding='utf-8') as f:
    f.write(seat_map_content)
