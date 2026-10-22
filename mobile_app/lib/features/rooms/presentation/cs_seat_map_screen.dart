import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
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
  final Set<String> _reportedSeats = {};
  List<String> _warningSeats = [];

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
    
    // Fetch reported seats (incidents)
    final incidents = await ApiClient.getIncidents(roomId: widget.roomId, status: 'open');
    final reported = <String>{};
    for (var inc in incidents) {
      if (inc['category'] == 'seat_damage' && inc['seat_ids'] != null) {
        if (inc['seat_ids'] is List) {
          for (var s in inc['seat_ids']) {
            reported.add(s.toString());
          }
        }
      }
    }

    // Fetch alerts for warning seats
    final alerts = await ApiClient.fetchAlerts(roomId: widget.roomId);
    final warnings = <String>{};
    for (var a in alerts) {
      if (a['seat_ids'] != null && a['seat_ids'] is List) {
        for (var s in a['seat_ids']) {
          warnings.add(s.toString());
        }
      } else if (a['seat_id'] != null) {
        warnings.add(a['seat_id'].toString());
      }
    }

    if (mounted) {
      setState(() {
        _occupiedSeats = occupied;
        _reportedSeats.addAll(reported);
        _warningSeats = warnings.toList();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final percentage = _occupiedSeats.isNotEmpty ? 100 : 0; // Tạm tính
    
    String title = widget.roomId;
    if (title.startsWith('seats_config_')) {
      title = title.replaceAll('seats_config_', '');
    }
    if (title.startsWith('room')) {
      title = title.replaceAll('room', 'Phòng chiếu ');
    }

    return Scaffold(
      body: SafeArea(
        child: _isLoading 
          ? const Center(child: CircularProgressIndicator())
          : ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            CSScreenHeader(
              title: 'Sơ đồ ghế - $title',
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
            
            CSSeatMap(
              showWarnings: true,
              selectionMode: false,
              occupiedSeats: _occupiedSeats,
              selectedSeats: const {},
              reportedSeats: _reportedSeats,
              warningSeats: _warningSeats,
              brokenSeats: const [],
              ignoredSeats: const [],
              onSeatTapped: null,
            ),
            const SizedBox(height: 22),
            CSPrimaryButton(
              label: 'Báo ghế hư',
              icon: Icons.report_problem_outlined,
              onPressed: () {
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
