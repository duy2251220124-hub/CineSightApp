import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';

class CSShowtimesScreen extends StatefulWidget {
  final ValueChanged<Map<String, dynamic>>? onMovieSelected;

  const CSShowtimesScreen({
    super.key,
    this.onMovieSelected,
  });

  @override
  State<CSShowtimesScreen> createState() => _CSShowtimesScreenState();
}

class _CSShowtimesScreenState extends State<CSShowtimesScreen> {
  bool _isLoading = true;
  String _selectedRoomFilter = 'all';
  String _searchQuery = '';
  List<Map<String, dynamic>> _showtimes = [];

  static List<Map<String, dynamic>> _buildFallbackShowtimes() {
    final now = DateTime.now();
    final dateStr =
        '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';

    final Map<String, List<Map<String, dynamic>>> schedules = {
      'room1': [
        {'start': '08:30', 'end': '10:15', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '10:25', 'end': '12:10', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '12:20', 'end': '14:05', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '14:15', 'end': '16:00', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '16:10', 'end': '17:55', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '18:05', 'end': '19:50', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '20:00', 'end': '22:00', 'duration': 120, 'movie': 'Spider-Man: Brand New Day'},
        {'start': '22:10', 'end': '00:10', 'duration': 120, 'movie': 'Spider-Man: Brand New Day'},
      ],
      'room2': [
        {'start': '08:30', 'end': '10:30', 'duration': 120, 'movie': 'Spider-Man: Brand New Day'},
        {'start': '10:40', 'end': '12:40', 'duration': 120, 'movie': 'The Odyssey'},
        {'start': '12:50', 'end': '14:50', 'duration': 120, 'movie': 'The Odyssey'},
        {'start': '15:00', 'end': '16:50', 'duration': 110, 'movie': 'Insidious: Out Of The Dark'},
        {'start': '17:00', 'end': '18:50', 'duration': 110, 'movie': 'Insidious: Out Of The Dark'},
        {'start': '19:00', 'end': '20:50', 'duration': 110, 'movie': 'Insidious: Out Of The Dark'},
        {'start': '21:00', 'end': '22:50', 'duration': 110, 'movie': 'Insidious: Out Of The Dark'},
      ],
      'room3': [
        {'start': '08:30', 'end': '10:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '10:30', 'end': '12:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '12:30', 'end': '14:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '14:30', 'end': '16:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '16:30', 'end': '18:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '18:30', 'end': '20:20', 'duration': 110, 'movie': 'Nghỉ Hè Sợ Nghỉ'},
        {'start': '20:30', 'end': '22:15', 'duration': 105, 'movie': "The Djinn's Curse"},
        {'start': '22:25', 'end': '00:10', 'duration': 105, 'movie': "The Djinn's Curse"},
      ],
      'room4': [
        {'start': '08:30', 'end': '10:20', 'duration': 110, 'movie': 'Insidious: Out Of The Dark'},
        {'start': '10:30', 'end': '12:25', 'duration': 115, 'movie': '(Rerun 2026) One Piece Film: Red'},
        {'start': '12:35', 'end': '14:20', 'duration': 105, 'movie': "The Djinn's Curse"},
        {'start': '14:30', 'end': '16:20', 'duration': 110, 'movie': 'The End Of Oasis'},
        {'start': '16:30', 'end': '18:15', 'duration': 105, 'movie': '2DDUB Paw Patrol'},
        {'start': '18:25', 'end': '20:10', 'duration': 105, 'movie': '2DDUB Crayon Shinchan'},
        {'start': '20:20', 'end': '22:10', 'duration': 110, 'movie': 'Whistle'},
        {'start': '22:20', 'end': '00:10', 'duration': 110, 'movie': 'Whistle'},
      ],
    };

    final List<Map<String, dynamic>> result = [];
    schedules.forEach((roomId, shows) {
      final roomNum = roomId.replaceAll('room', '');
      for (final s in shows) {
        final showId = '${dateStr}T${s['start']}';
        result.add({
          'id': showId,
          'show_id': showId,
          'room_id': roomId,
          'room_name': 'Phòng chiếu $roomNum',
          'movie_name': s['movie'],
          'start_time': s['start'],
          'end_time': s['end'],
          'duration_minutes': s['duration'],
          'break_minutes': 10,
          'date': dateStr,
        });
      }
    });
    return result;
  }

  @override
  void initState() {
    super.initState();
    _loadShowtimes();
  }

  Future<void> _loadShowtimes() async {
    final remote = await ApiClient.fetchShowtimes();
    if (!mounted) return;
    if (remote.isNotEmpty) {
      setState(() {
        _showtimes = remote.map<Map<String, dynamic>>((item) {
          final m = Map<String, dynamic>.from(item as Map);
          m['id'] = m['show_id'] ?? m['id'];
          return m;
        }).toList();
        _isLoading = false;
      });
    } else {
      setState(() {
        _showtimes = _buildFallbackShowtimes();
        _isLoading = false;
      });
    }
  }

  String _formatDuration(int mins) {
    final h = mins ~/ 60;
    final m = mins % 60;
    return '${h}h${m.toString().padLeft(2, '0')}p ($mins phút)';
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _showtimes.where((s) {
      if (_selectedRoomFilter != 'all' && s['room_id'] != _selectedRoomFilter) {
        return false;
      }
      if (_searchQuery.trim().isNotEmpty) {
        final q = _searchQuery.toLowerCase();
        final movie = (s['movie_name'] ?? '').toString().toLowerCase();
        final showId = (s['show_id'] ?? '').toString().toLowerCase();
        return movie.contains(q) || showId.contains(q);
      }
      return true;
    }).toList();

    final roomFilters = [
      {'id': 'all', 'label': 'Tất cả (4 phòng)'},
      {'id': 'room1', 'label': 'Phòng 1'},
      {'id': 'room2', 'label': 'Phòng 2'},
      {'id': 'room3', 'label': 'Phòng 3'},
      {'id': 'room4', 'label': 'Phòng 4'},
    ];

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Lịch chiếu phim',
              subtitle: 'Mở cửa 08:30 · Phim 1h45p–2h00p · Nghỉ 10p',
              trailingIcon: Icons.schedule,
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: TextField(
                onChanged: (val) => setState(() => _searchQuery = val),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  hintText: 'Tìm theo tên phim hoặc giờ chiếu...',
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 36,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 10),
                itemCount: roomFilters.length,
                separatorBuilder: (_, __) => const SizedBox(width: 6),
                itemBuilder: (context, idx) {
                  final f = roomFilters[idx];
                  final isSelected = _selectedRoomFilter == f['id'];
                  return ChoiceChip(
                    label: Text(
                      f['label']!,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: isSelected ? Colors.white : CSAppColors.muted,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: CSAppColors.primary,
                    backgroundColor: CSAppColors.surface,
                    onSelected: (_) => setState(() => _selectedRoomFilter = f['id']!),
                  );
                },
              ),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      itemCount: filtered.length,
                      itemBuilder: (context, index) {
                        final s = filtered[index];
                        final movieName = s['movie_name']?.toString() ?? 'Suất chiếu';
                        final roomName = s['room_name']?.toString() ?? s['room_id']?.toString() ?? 'Phòng 1';
                        final startTime = s['start_time']?.toString() ?? '08:30';
                        final endTime = s['end_time']?.toString() ?? '10:15';
                        final duration = (s['duration_minutes'] as int?) ?? 105;
                        final breakMins = (s['break_minutes'] as int?) ?? 10;
                        final showId = s['show_id']?.toString() ?? s['id']?.toString() ?? '';

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: CSAppCard(
                            onTap: () => widget.onMovieSelected?.call(s),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        movieName,
                                        style: const TextStyle(
                                          fontSize: 15,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    CSStatusTag(
                                      text: '$startTime - $endTime',
                                      color: CSAppColors.primary,
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  '$roomName · Thời lượng: ${_formatDuration(duration)} · Nghỉ chuyển suất: ${breakMins}p',
                                  style: const TextStyle(
                                    color: CSAppColors.muted,
                                    fontSize: 11,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  'Mã suất: $showId',
                                  style: const TextStyle(
                                    color: CSAppColors.muted,
                                    fontSize: 10,
                                  ),
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
