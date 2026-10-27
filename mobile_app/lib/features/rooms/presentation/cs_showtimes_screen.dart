import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
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
  late DateTime _selectedDate;
  List<Map<String, dynamic>> _showtimes = [];

  static String _toDateStr(DateTime dt) {
    return '${dt.year.toString().padLeft(4, '0')}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  }

  static String _formatDisplayDate(DateTime dt) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final target = DateTime(dt.year, dt.month, dt.day);
    final diff = target.difference(today).inDays;

    final dmy =
        '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    if (diff == 0) return 'Hôm nay, $dmy';
    if (diff == -1) return 'Hôm qua, $dmy';
    if (diff == 1) return 'Ngày mai, $dmy';
    return 'Ngày $dmy';
  }

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _selectedDate = DateTime(now.year, now.month, now.day);
    _loadShowtimes();
  }

  Future<void> _loadShowtimes() async {
    setState(() => _isLoading = true);
    final dateStr = _toDateStr(_selectedDate);
    try {
      final remote = await ApiClient.fetchShowtimes(date: dateStr);
      if (!mounted) return;
      setState(() {
        _showtimes = remote.map<Map<String, dynamic>>((item) {
          final m = Map<String, dynamic>.from(item as Map);
          m['id'] = m['show_id'] ?? m['id'];
          return m;
        }).toList();
        _isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _showtimes = [];
        _isLoading = false;
      });
    }
  }

  void _selectDate(DateTime newDate) {
    final normalized = DateTime(newDate.year, newDate.month, newDate.day);
    if (_toDateStr(normalized) == _toDateStr(_selectedDate)) return;
    setState(() {
      _selectedDate = normalized;
    });
    _loadShowtimes();
  }

  Future<void> _pickCustomDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(now.year - 1, 1, 1),
      lastDate: DateTime(now.year + 1, 12, 31),
      helpText: 'CHỌN NGÀY CHIẾU PHIM',
      cancelText: 'Hủy',
      confirmText: 'Xem lịch',
    );
    if (picked != null) {
      _selectDate(picked);
    }
  }

  String _formatDuration(int mins) {
    final h = mins ~/ 60;
    final m = mins % 60;
    return '${h}h${m.toString().padLeft(2, '0')}p ($mins phút)';
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final tomorrow = today.add(const Duration(days: 1));

    final selectedDateStr = _toDateStr(_selectedDate);
    final isYesterday = selectedDateStr == _toDateStr(yesterday);
    final isToday = selectedDateStr == _toDateStr(today);
    final isTomorrow = selectedDateStr == _toDateStr(tomorrow);
    final isCustomDate = !isYesterday && !isToday && !isTomorrow;

    final filtered = _showtimes.where((s) {
      // Đảm bảo chỉ hiển thị đúng ngày đang chọn
      final itemDate = (s['date'] ?? (s['show_id']?.toString().split('T').first ?? '')).toString();
      if (itemDate.isNotEmpty && itemDate != selectedDateStr) {
        return false;
      }
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
      {'id': 'all', 'label': 'Tất cả phòng'},
      {'id': 'room1', 'label': 'Phòng chiếu số 1'},
      {'id': 'room2', 'label': 'Phòng chiếu số 2'},
      {'id': 'room3', 'label': 'Phòng chiếu số 3'},
      {'id': 'room4', 'label': 'Phòng chiếu số 4'},
    ];

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Lịch chiếu phim',
              subtitle: '${_formatDisplayDate(_selectedDate)} · ${filtered.length} suất chiếu',
              trailingIcon: Icons.calendar_month_outlined,
              onTrailing: _pickCustomDate,
            ),

            // Thanh chọn Ngày (Hôm qua / Hôm nay / Ngày mai / Chọn lịch)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: SizedBox(
                height: 36,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    ChoiceChip(
                      label: Text(
                        'Hôm qua (${yesterday.day.toString().padLeft(2, '0')}/${yesterday.month.toString().padLeft(2, '0')})',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: isYesterday ? Colors.white : CSAppColors.muted,
                        ),
                      ),
                      selected: isYesterday,
                      selectedColor: CSAppColors.primary,
                      backgroundColor: CSAppColors.surface,
                      onSelected: (_) => _selectDate(yesterday),
                    ),
                    const SizedBox(width: 6),
                    ChoiceChip(
                      label: Text(
                        'Hôm nay (${today.day.toString().padLeft(2, '0')}/${today.month.toString().padLeft(2, '0')})',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: isToday ? Colors.white : CSAppColors.muted,
                        ),
                      ),
                      selected: isToday,
                      selectedColor: CSAppColors.primary,
                      backgroundColor: CSAppColors.surface,
                      onSelected: (_) => _selectDate(today),
                    ),
                    const SizedBox(width: 6),
                    ChoiceChip(
                      label: Text(
                        'Ngày mai (${tomorrow.day.toString().padLeft(2, '0')}/${tomorrow.month.toString().padLeft(2, '0')})',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: isTomorrow ? Colors.white : CSAppColors.muted,
                        ),
                      ),
                      selected: isTomorrow,
                      selectedColor: CSAppColors.primary,
                      backgroundColor: CSAppColors.surface,
                      onSelected: (_) => _selectDate(tomorrow),
                    ),
                    const SizedBox(width: 6),
                    ActionChip(
                      avatar: Icon(
                        Icons.event_outlined,
                        size: 14,
                        color: isCustomDate ? Colors.white : CSAppColors.primary,
                      ),
                      label: Text(
                        isCustomDate
                            ? '${_selectedDate.day.toString().padLeft(2, '0')}/${_selectedDate.month.toString().padLeft(2, '0')}/${_selectedDate.year}'
                            : 'Chọn ngày khác',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: isCustomDate ? Colors.white : CSAppColors.muted,
                        ),
                      ),
                      backgroundColor: isCustomDate ? CSAppColors.primary : CSAppColors.surface,
                      onPressed: _pickCustomDate,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),

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
                separatorBuilder: (context, index) => const SizedBox(width: 6),
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
                  : filtered.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(
                                  Icons.event_busy_outlined,
                                  size: 48,
                                  color: CSAppColors.muted,
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  'Không có suất chiếu nào trong ${_formatDisplayDate(_selectedDate).toLowerCase()}.',
                                  style: const TextStyle(color: CSAppColors.muted, fontSize: 13),
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 12),
                                OutlinedButton.icon(
                                  onPressed: _loadShowtimes,
                                  icon: const Icon(Icons.refresh, size: 16),
                                  label: const Text('Tải lại'),
                                  style: OutlinedButton.styleFrom(
                                    foregroundColor: CSAppColors.primary,
                                    side: const BorderSide(color: CSAppColors.primary),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                      : RefreshIndicator(
                          onRefresh: _loadShowtimes,
                          child: ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            itemCount: filtered.length,
                            itemBuilder: (context, index) {
                              final s = filtered[index];
                              final movieName = s['movie_name']?.toString() ?? 'Suất chiếu';
                              final roomName = formatRoomName(s['room_id']?.toString() ?? s['room_name']?.toString());
                              final startTime = s['start_time']?.toString() ?? '08:30';
                              final endTime = s['end_time']?.toString() ?? '10:15';
                              final duration = (s['duration_minutes'] as int?) ?? 105;
                              final breakMins = (s['break_minutes'] as int?) ?? 15;
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
            ),
          ],
        ),
      ),
    );
  }
}
