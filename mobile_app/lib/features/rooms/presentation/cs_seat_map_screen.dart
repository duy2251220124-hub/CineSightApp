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
  final void Function(String roomId, String showId, String movieTitle)? onGoToScanner;

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
  int get _totalSeats => _cleanRoomId.toLowerCase().contains('room3') || _cleanRoomId.contains('3') ? 132 : 136;

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
    if (widget.showId.isNotEmpty && widget.showId != 'auto' && widget.showId != 'all') {
      _selectedShowId = widget.showId;
    }
    _initRoomData();
  }

  Future<void> _initRoomData() async {
    setState(() => _isLoading = true);

    try {
      // Nếu showId truyền vào có kèm ngày (yyyy-MM-ddTHH:mm) thì lấy ngày đó, ngược lại mặc định lấy ngày hôm nay
      final now = DateTime.now();
      final todayStr =
          '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
      final targetDate = (_selectedShowId.contains('T') && _selectedShowId.length >= 10)
          ? _selectedShowId.substring(0, 10)
          : todayStr;

      var rawShows = await ApiClient.fetchShowtimes(roomId: _cleanRoomId, date: targetDate);
      if (rawShows.isEmpty && targetDate != todayStr) {
        rawShows = await ApiClient.fetchShowtimes(roomId: _cleanRoomId, date: todayStr);
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
          // Chọn suất chiếu đầu tiên hoặc gần nhất trong ngày của phòng
          matched = _roomShowtimes.first;
        }
        _selectedShowId = '${matched['show_id'] ?? ''}';
        _selectedMovieTitle = '${matched['movie_name'] ?? matched['title'] ?? ''}';
      }
    } catch (_) {
      // Bỏ qua lỗi mạng tạm thời
    }

    await _loadSeatStatus();
  }

  Future<void> _loadSeatStatus() async {
    setState(() => _isLoading = true);

    // 1. Lấy danh sách vé đã soát của phòng + suất chiếu đang chọn
    final List<String> occupied = [];
    if (_selectedShowId.isNotEmpty && _selectedShowId != 'auto' && _selectedShowId != 'all') {
      final tickets = await ApiClient.fetchTickets(_cleanRoomId, _selectedShowId);
      for (var t in tickets) {
        if (t['seat'] != null) occupied.add(t['seat'].toString());
        if (t['seat_id'] != null) occupied.add(t['seat_id'].toString());
      }
    }

    // 2. Lấy danh sách ghế hỏng (incidents có category == 'seat_damage' và status == 'open')
    final incidents = await ApiClient.getIncidents(roomId: _cleanRoomId, status: 'open');
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

    // 3. Lấy danh sách ghế có cảnh báo AI của phòng (lọc theo suất nếu có)
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
                    Navigator.pop(addCtx);     // Đóng CSAddIncidentScreen
                    Navigator.pop(damagedCtx); // Đóng CSDamagedSeatScreen về lại CSSeatMapScreen
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
    final start = s['start_time']?.toString() ??
        (s['show_id']?.toString().contains('T') == true
            ? s['show_id'].toString().split('T')[1]
            : s['show_id']?.toString() ?? '');
    final movie = s['movie_name']?.toString() ?? s['title']?.toString() ?? '';
    return movie.isNotEmpty ? '$start · $movie' : start;
  }

  @override
  Widget build(BuildContext context) {
    final int percentage = ((_occupiedSeats.length / _totalSeats) * 100).round().clamp(0, 100);

    final title = formatRoomName(_cleanRoomId);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadSeatStatus,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            children: [
              CSScreenHeader(
                title: 'Sơ đồ ghế - $title',
                subtitle: '$_totalSeats ghế · Chạm suất chiếu bên dưới để xem trạng thái ghế',
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
                            color: isSelected ? Colors.white : CSAppColors.muted,
                          ),
                        ),
                        selected: isSelected,
                        selectedColor: CSAppColors.primary,
                        backgroundColor: CSAppColors.surface,
                        onSelected: (_) {
                          setState(() {
                            _selectedShowId = sId;
                            _selectedMovieTitle = '${s['movie_name'] ?? s['title'] ?? ''}';
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
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Mã suất: ${_selectedShowId.isNotEmpty ? _selectedShowId : "Chưa chọn"} | ${formatRoomName(_cleanRoomId)}',
                      style: const TextStyle(
                        color: CSAppColors.muted,
                        fontSize: 11,
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
                            fontSize: 11,
                            color: CSAppColors.primary,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 8),

              // Ghi chú màu ghế trực quan
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 4),
                child: Wrap(
                  spacing: 12,
                  runSpacing: 6,
                  children: [
                    _SeatLegendItem(color: Color(0xFF1E293B), label: 'Còn trống'),
                    _SeatLegendItem(color: CSAppColors.primary, label: 'Đã soát vé'),
                    _SeatLegendItem(color: CSAppColors.warning, label: 'Báo hỏng'),
                    _SeatLegendItem(color: CSAppColors.danger, label: 'Cảnh báo AI'),
                  ],
                ),
              ),

              const SizedBox(height: 12),

              CSAppCard(
                child: Column(
                  children: [
                    // Lưới hiển thị ghế (kèm vòm màn hình chiếu chuẩn camera bên trong)
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
                              ScaffoldMessenger.of(context).hideCurrentSnackBar();
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
                                  content: Text('Vị trí: $seatId · $statusText'),
                                  duration: const Duration(seconds: 1),
                                ),
                              );
                            },
                          ),
                  ],
                ),
              ),

              const SizedBox(height: 18),
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
                            _selectedShowId.isNotEmpty ? _selectedShowId : 'auto',
                            _selectedMovieTitle,
                          );
                        },
                        icon: const Icon(Icons.qr_code_scanner, size: 18),
                        label: const Text('Soát vé phòng này'),
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
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
            border: Border.all(color: Colors.white24, width: 0.5),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 10, color: CSAppColors.muted),
        ),
      ],
    );
  }
}
