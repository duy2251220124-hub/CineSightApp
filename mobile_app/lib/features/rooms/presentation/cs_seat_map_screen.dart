import 'package:flutter/material.dart';

import 'dart:convert';

import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/utils/show_id_utils.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/features/rooms/presentation/widgets/cs_seat_map.dart';
import 'package:mobile_app/features/alerts/presentation/cs_damaged_seat_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_add_incident_screen.dart';

class CSSeatMapScreen extends StatefulWidget {
  final String roomId;
  final String showId;
  final VoidCallback? onReportDamagedSeat;
  final void Function(String roomId, String showId, String movieTitle)?
  onGoToScanner;

  const CSSeatMapScreen({
    super.key,
    required this.roomId,
    required this.showId,
    this.onReportDamagedSeat,
    this.onGoToScanner,
  });

  @override
  State<CSSeatMapScreen> createState() => _CSSeatMapScreenState();
}

class _CSSeatMapScreenState extends State<CSSeatMapScreen> {
  int get _totalSeats =>
      _cleanRoomId.toLowerCase().contains('room3') || _cleanRoomId.contains('3')
      ? 132
      : 136;

  bool _isLoading = true;
  late String _cleanRoomId;
  String _selectedShowId = '';
  String _selectedMovieTitle = '';
  List<Map<String, dynamic>> _roomShowtimes = [];

  List<String> _occupiedSeats = [];
  final Set<String> _reportedSeats = {};
  List<String> _warningSeats = [];

  @override
  void initState() {
    super.initState();
    _cleanRoomId = widget.roomId.replaceAll('seats_config_', '').trim();
    if (widget.showId.isNotEmpty &&
        widget.showId != 'auto' &&
        widget.showId != 'all') {
      _selectedShowId = widget.showId;
    }
    _initRoomData();
  }

  Future<void> _initRoomData() async {
    setState(() => _isLoading = true);

    try {
      final now = DateTime.now();
      final todayStr =
          '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
      final targetDate =
          (_selectedShowId.contains('T') && _selectedShowId.length >= 10)
          ? _selectedShowId.substring(0, 10)
          : todayStr;

      var rawShows = await ApiClient.fetchShowtimes(
        roomId: _cleanRoomId,
        date: targetDate,
      );
      if (rawShows.isEmpty && targetDate != todayStr) {
        rawShows = await ApiClient.fetchShowtimes(
          roomId: _cleanRoomId,
          date: todayStr,
        );
      }

      final parsedShows = rawShows
          .map<Map<String, dynamic>>((e) => Map<String, dynamic>.from(e as Map))
          .toList();

      _roomShowtimes = parsedShows;

      if (_roomShowtimes.isNotEmpty) {
        Map<String, dynamic> matched = {};
        if (_selectedShowId.isNotEmpty) {
          matched = _roomShowtimes.firstWhere(
            (s) => '${s['show_id']}' == _selectedShowId,
            orElse: () => {},
          );
        }
        if (matched.isEmpty) {
          matched = _roomShowtimes.first;
        }
        _selectedShowId = '${matched['show_id'] ?? ''}';
        _selectedMovieTitle =
            '${matched['movie_name'] ?? matched['title'] ?? ''}';
      }
    } catch (_) {
      // Bỏ qua lỗi mạng tạm thời
    }

    await _loadSeatStatus();
  }

  Future<void> _loadSeatStatus() async {
    setState(() => _isLoading = true);

    final List<String> occupied = [];
    if (_selectedShowId.isNotEmpty &&
        _selectedShowId != 'auto' &&
        _selectedShowId != 'all') {
      final tickets = await ApiClient.fetchTickets(
        _cleanRoomId,
        _selectedShowId,
      );
      for (var t in tickets) {
        if (t['seat'] != null) occupied.add(t['seat'].toString());
        if (t['seat_id'] != null) occupied.add(t['seat_id'].toString());
      }
    }

    final incidents = await ApiClient.getIncidents(
      roomId: _cleanRoomId,
      status: 'open',
    );
    final reported = <String>{};
    for (var inc in incidents) {
      if (inc['category'] == 'seat_damage' && inc['seat_ids'] != null) {
        final rawSeats = inc['seat_ids'];
        if (rawSeats is List) {
          for (var s in rawSeats) {
            reported.add(s.toString().trim());
          }
        } else if (rawSeats is String && rawSeats.trim().isNotEmpty) {
          try {
            final parsed = jsonDecode(rawSeats);
            if (parsed is List) {
              for (var s in parsed) {
                reported.add(s.toString().trim());
              }
            }
          } catch (_) {
            for (var s in rawSeats.split(RegExp(r'[,; ]+'))) {
              if (s.trim().isNotEmpty) reported.add(s.trim());
            }
          }
        }
      }
    }

    final alerts = await ApiClient.fetchAlerts(roomId: _cleanRoomId);
    final warnings = <String>{};
    for (var a in alerts) {
      if (_selectedShowId.isNotEmpty &&
          a['show_id'] != null &&
          a['show_id'].toString() != _selectedShowId) {
        continue;
      }
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
        _reportedSeats
          ..clear()
          ..addAll(reported);
        _warningSeats = warnings.toList();
        _isLoading = false;
      });
    }
  }

  Future<void> _handleReportDamagedSeatFlow() async {
    if (widget.onReportDamagedSeat != null) {
      widget.onReportDamagedSeat!();
      return;
    }

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (damagedCtx) => CSDamagedSeatScreen(
          roomId: _cleanRoomId,
          onAddPhoto: (selectedSeats) async {
            await Navigator.push(
              damagedCtx,
              MaterialPageRoute(
                builder: (addCtx) => CSAddIncidentScreen(
                  reportedSeats: selectedSeats,
                  roomId: _cleanRoomId,
                  showId: _selectedShowId.isNotEmpty ? _selectedShowId : null,
                  initialCategory: 'seat_damage',
                  onIncidentAdded: () {
                    Navigator.pop(addCtx);
                    Navigator.pop(damagedCtx);
                  },
                ),
              ),
            );
          },
        ),
      ),
    );

    if (mounted) {
      await _loadSeatStatus();
    }
  }

  String _formatShowLabel(Map<String, dynamic> s) {
    final start =
        s['start_time']?.toString() ??
        (s['show_id']?.toString().contains('T') == true
            ? s['show_id'].toString().split('T')[1]
            : s['show_id']?.toString() ?? '');
    final movie = s['movie_name']?.toString() ?? s['title']?.toString() ?? '';
    return movie.isNotEmpty ? '$start · $movie' : start;
  }

  String _formatFriendlyShowId(String raw) {
    if (raw.isEmpty) return 'Chưa chọn';
    if (raw.contains('T')) {
      final parts = raw.split('T');
      final datePart = parts[0];
      final timePart = parts.length > 1 ? parts[1] : '';
      final d = datePart.split('-');
      if (d.length == 3) {
        return '$timePart (${d[2]}/${d[1]}/${d[0]})';
      }
      return timePart;
    }
    return raw;
  }

  @override
  Widget build(BuildContext context) {
    final int percentage = ((_occupiedSeats.length / _totalSeats) * 100)
        .round()
        .clamp(0, 100);
    final title = formatRoomName(_cleanRoomId);

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          onRefresh: _loadSeatStatus,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
            children: [
              CSScreenHeader(
                title: 'Sơ đồ ghế - $title',
                subtitle:
                    'Tổng $_totalSeats ghế · Chạm suất chiếu bên dưới để xem trạng thái',
                trailingIcon: Icons.refresh,
                onTrailing: _loadSeatStatus,
              ),

              // Bộ chọn suất chiếu trong phòng
              if (_roomShowtimes.isNotEmpty) ...[
                SizedBox(
                  height: 36,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: _roomShowtimes.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 6),
                    itemBuilder: (context, idx) {
                      final s = _roomShowtimes[idx];
                      final sId = '${s['show_id'] ?? ''}';
                      final isSelected = sId == _selectedShowId;
                      return ChoiceChip(
                        label: Text(
                          _formatShowLabel(s),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: isSelected
                                ? Colors.white
                                : CSAppColors.muted,
                          ),
                        ),
                        selected: isSelected,
                        selectedColor: CSAppColors.primary,
                        backgroundColor: CSAppColors.surface,
                        side: BorderSide(
                          color: isSelected
                              ? CSAppColors.primary
                              : CSAppColors.border,
                        ),
                        onSelected: (_) {
                          setState(() {
                            _selectedShowId = sId;
                            _selectedMovieTitle =
                                '${s['movie_name'] ?? s['title'] ?? ''}';
                          });
                          CSActiveShowtime.update(
                            roomId: _cleanRoomId,
                            showId: _selectedShowId,
                            movieTitle: _selectedMovieTitle,
                          );
                          _loadSeatStatus();
                        },
                      );
                    },
                  ),
                ),
                const SizedBox(height: 10),
              ],

              CSAppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _selectedMovieTitle.isNotEmpty
                          ? _selectedMovieTitle
                          : 'Suất chiếu hiện tại',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 15,
                        color: CSAppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Suất chiếu: ${_formatFriendlyShowId(_selectedShowId)}  |  $title',
                      style: TextStyle(
                        color: CSAppColors.muted,
                        fontSize: 11.5,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: percentage / 100,
                              backgroundColor: CSAppColors.border,
                              color: CSAppColors.primary,
                              minHeight: 6,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '$percentage% (${_occupiedSeats.length}/$_totalSeats)',
                          style: const TextStyle(
                            fontSize: 11.5,
                            color: CSAppColors.primary,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 10),

              // Ghi chú màu ghế trực quan — CĂN GIỮA CÂN ĐỐI HOÀN HẢO
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  vertical: 8,
                  horizontal: 10,
                ),
                decoration: BoxDecoration(
                  color: CSAppColors.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: CSAppColors.border,
                  ),
                ),
                alignment: Alignment.center,
                child: Wrap(
                  alignment: WrapAlignment.center,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 16,
                  runSpacing: 8,
                  children: [
                    _SeatLegendItem(
                      color: CSAppColors.seatEmpty,
                      label: 'Còn trống',
                    ),
                    const _SeatLegendItem(
                      color: CSAppColors.primary,
                      label: 'Đã soát vé',
                    ),
                    const _SeatLegendItem(
                      color: CSAppColors.warning,
                      label: 'Báo hỏng',
                    ),
                    const _SeatLegendItem(
                      color: CSAppColors.danger,
                      label: 'Cảnh báo AI',
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 10),

              CSAppCard(
                child: Column(
                  children: [
                    _isLoading
                        ? const Padding(
                            padding: EdgeInsets.symmetric(vertical: 40),
                            child: Center(child: CircularProgressIndicator()),
                          )
                        : CSSeatMap(
                            roomId: _cleanRoomId,
                            showWarnings: true,
                            occupiedSeats: _occupiedSeats,
                            warningSeats: _warningSeats,
                            brokenSeats: _reportedSeats.toList(),
                            reportedSeats: _reportedSeats,
                            onSeatTapped: (seatId) {
                              ScaffoldMessenger.of(context)
                                  .hideCurrentSnackBar();
                              final isOcc = _occupiedSeats.contains(seatId);
                              final isRep = _reportedSeats.contains(seatId);
                              final isWarn = _warningSeats.contains(seatId);

                              String statusText = 'Ghế trống';
                              if (isWarn) {
                                statusText = '⚠️ Cảnh báo bất thường AI';
                              } else if (isRep) {
                                statusText = '🛠️ Đã báo hỏng / Đang bảo trì';
                              } else if (isOcc) {
                                statusText = '✅ Đã soát vé hợp lệ';
                              }

                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Vị trí: $seatId · $statusText',
                                  ),
                                  duration: const Duration(seconds: 1),
                                ),
                              );
                            },
                          ),
                  ],
                ),
              ),

              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: CSPrimaryButton(
                      label: 'Báo ghế hư',
                      icon: Icons.report_problem_outlined,
                      onPressed: _handleReportDamagedSeatFlow,
                    ),
                  ),
                  if (widget.onGoToScanner != null) ...[
                    const SizedBox(width: 10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () {
                          widget.onGoToScanner!(
                            _cleanRoomId,
                            _selectedShowId.isNotEmpty
                                ? _selectedShowId
                                : 'auto',
                            _selectedMovieTitle,
                          );
                        },
                        icon: const Icon(Icons.qr_code_scanner, size: 18),
                        label: const Text('Soát vé'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: CSAppColors.primary,
                          side: const BorderSide(color: CSAppColors.primary),
                          minimumSize: const Size(double.infinity, 48),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _SeatLegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _SeatLegendItem({required this.color, required this.label});

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
            borderRadius: BorderRadius.circular(3),
            border: Border.all(color: CSAppColors.border, width: 0.8),
          ),
        ),
        const SizedBox(width: 5),
        Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
            color: CSAppColors.textSecondary,
          ),
        ),
      ],
    );
  }
}
