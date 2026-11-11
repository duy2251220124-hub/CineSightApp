import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/features/alerts/presentation/cs_warning_detail_screen.dart';
import 'package:mobile_app/core/utils/room_utils.dart';

class CSWarningScreen extends StatefulWidget {
  final ValueChanged<int>? onNavigationChanged;
  final ValueChanged<Map<String, dynamic>>? onWarningSelected;
  final VoidCallback? onIgnoreAll;

  const CSWarningScreen({
    super.key,
    this.onNavigationChanged,
    this.onWarningSelected,
    this.onIgnoreAll,
  });

  @override
  State<CSWarningScreen> createState() => CSWarningScreenState();
}

class CSWarningScreenState extends State<CSWarningScreen> {
  List<dynamic> _alerts = [];
  bool _isLoading = true;
  final Set<String> _expandedRooms = {};
  bool _isBatchResolving = false;

  @override
  void initState() {
    super.initState();
    loadAlerts();
  }

  /// Hàm công khai cho phép HomeShell gọi tải lại từ ngoài
  Future<void> loadAlerts() async {
    final alerts = await ApiClient.fetchAlerts();
    if (mounted) {
      setState(() {
        _alerts = alerts;
        _isLoading = false;
      });
    }
  }

  String _formatRoomName(String? rId) => formatRoomName(rId);

  Color _color(String type) {
    if (type == 'illegal_occupant') return CSAppColors.danger;
    if (type == 'missing_guest') return CSAppColors.warning;
    return CSAppColors.primary;
  }

  Map<String, List<dynamic>> _groupByRoomAndShow() {
    final Map<String, List<dynamic>> groups = {};
    for (final a in _alerts) {
      final key = '${a['room_id']}__${a['show_id']}';
      groups.putIfAbsent(key, () => []).add(a);
    }
    return groups;
  }

  Future<void> _handleResolveRoom(String roomId, String showId, String roomDisplayName, int count) async {
    setState(() => _isBatchResolving = true);
    final messenger = ScaffoldMessenger.of(context);
    final success = await ApiClient.resolveRoomAlerts(roomId, showId);
    if (!mounted) return;
    setState(() => _isBatchResolving = false);
    if (success) {
      messenger.showSnackBar(
        SnackBar(
          content: Text('Đã xử lý xong toàn bộ $count cảnh báo cho $roomDisplayName!'),
          backgroundColor: CSAppColors.success,
        ),
      );
      loadAlerts();
    } else {
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Không thể xử lý hàng loạt, vui lòng thử lại!'),
          backgroundColor: CSAppColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final grouped = _groupByRoomAndShow();
    final bool isLight = CSAppColors.isLight;

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          onRefresh: loadAlerts,
          child: Column(
            children: [
              // Banner tiêu đề Cảnh báo AI
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: _alerts.isNotEmpty
                      ? CSAppColors.danger.withValues(alpha: 0.12)
                      : CSAppColors.surface,
                  border: Border(
                    bottom: BorderSide(
                      color: _alerts.isNotEmpty ? CSAppColors.danger : CSAppColors.border,
                      width: 1.5,
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      _alerts.isNotEmpty ? Icons.notifications_active : Icons.check_circle_outline,
                      color: _alerts.isNotEmpty ? CSAppColors.danger : CSAppColors.success,
                      size: 26,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _alerts.isNotEmpty
                                ? 'CẢNH BÁO TỪ HỆ THỐNG AI (${grouped.length} PHÒNG • ${_alerts.length} GHẾ)'
                                : 'HỆ THỐNG AN TOÀN',
                            style: TextStyle(
                              color: _alerts.isNotEmpty ? CSAppColors.danger : CSAppColors.success,
                              fontWeight: FontWeight.w800,
                              fontSize: 13,
                              letterSpacing: 0.8,
                            ),
                          ),
                          Text(
                            _alerts.isNotEmpty
                                ? 'Phát hiện chênh lệch đối soát qua camera phòng chiếu'
                                : 'Không phát hiện vi phạm nào trong các phòng chiếu',
                            style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: 'Tải lại',
                      icon: Icon(Icons.refresh, size: 20, color: CSAppColors.textPrimary),
                      onPressed: () {
                        setState(() => _isLoading = true);
                        loadAlerts();
                      },
                    ),
                  ],
                ),
              ),

              // Danh sách cảnh báo gom nhóm theo phòng
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _alerts.isEmpty
                        ? ListView(
                            children: [
                              Padding(
                                padding: const EdgeInsets.symmetric(vertical: 80, horizontal: 20),
                                child: Column(
                                  children: [
                                    const Icon(Icons.verified_user_outlined, color: CSAppColors.success, size: 54),
                                    const SizedBox(height: 12),
                                    Text(
                                      'Không có cảnh báo vi phạm nào!',
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 16,
                                        color: CSAppColors.textPrimary,
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      'Mọi vị trí ngồi trong rạp đều khớp với vé đã soát.',
                                      style: TextStyle(color: CSAppColors.muted, fontSize: 12),
                                      textAlign: TextAlign.center,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          )
                        : ListView(
                            padding: const EdgeInsets.fromLTRB(12, 12, 12, 110),
                            children: grouped.entries.map((entry) {
                              final groupKey = entry.key;
                              final roomAlerts = entry.value;
                              final first = roomAlerts.first;
                              final roomId = first['room_id']?.toString() ?? '';
                              final showId = first['show_id']?.toString() ?? '';
                              final roomName = _formatRoomName(roomId);
                              final timeDisplay = showId.contains('T') ? showId.split('T')[1] : showId;

                              // 3 chỉ số nghiệp vụ
                              final scannedTickets = first['scanned_tickets_count'] ?? 0;
                              final detectedPeople = first['detected_people_count'] ?? 0;
                              final totalRoomAlerts = roomAlerts.length;

                              final isExpanded = _expandedRooms.contains(groupKey);

                              return Padding(
                                padding: const EdgeInsets.only(bottom: 14),
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: CSAppColors.surface,
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: CSAppColors.danger.withValues(alpha: 0.6),
                                      width: 1.5,
                                    ),
                                    boxShadow: [
                                      BoxSideShadow(
                                        color: Colors.black.withValues(alpha: isLight ? 0.06 : 0.25),
                                        blurRadius: 8,
                                        offset: const Offset(0, 3),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      // Header nhóm phòng
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                        decoration: BoxDecoration(
                                          color: CSAppColors.danger.withValues(alpha: 0.12),
                                          borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
                                        ),
                                        child: Row(
                                          children: [
                                            const Icon(Icons.meeting_room_outlined, color: CSAppColors.danger, size: 20),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(
                                                '$roomName • Suất $timeDisplay',
                                                style: TextStyle(
                                                  fontWeight: FontWeight.w800,
                                                  fontSize: 14,
                                                  color: CSAppColors.textPrimary,
                                                ),
                                              ),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: CSAppColors.danger,
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                '$totalRoomAlerts cảnh báo',
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),

                                      // 3 Chỉ số nghiệp vụ cốt lõi
                                      Padding(
                                        padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
                                        child: Row(
                                          children: [
                                            Expanded(
                                              child: _buildMetricTile(
                                                label: 'Vé đã quét',
                                                value: '$scannedTickets',
                                                icon: Icons.confirmation_number_outlined,
                                                color: CSAppColors.primary,
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: _buildMetricTile(
                                                label: 'Trong rạp',
                                                value: '$detectedPeople',
                                                icon: Icons.groups_outlined,
                                                color: isLight ? const Color(0xFF0284C7) : Colors.cyanAccent,
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: _buildMetricTile(
                                                label: 'Ghế vi phạm',
                                                value: '$totalRoomAlerts',
                                                icon: Icons.warning_amber_rounded,
                                                color: CSAppColors.danger,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),

                                      // Danh sách Chip các ghế cảnh báo
                                      Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                        child: Wrap(
                                          spacing: 6,
                                          runSpacing: 6,
                                          children: roomAlerts.map((warning) {
                                            final atype = warning['alert_type']?.toString() ?? '';
                                            final sName = warning['seat_id']?.toString() ?? 'N/A';
                                            final isIll = atype == 'illegal_occupant';
                                            final c = isIll ? CSAppColors.danger : CSAppColors.warning;
                                            return Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                              decoration: BoxDecoration(
                                                color: c.withValues(alpha: 0.15),
                                                borderRadius: BorderRadius.circular(6),
                                                border: Border.all(color: c.withValues(alpha: 0.6)),
                                              ),
                                              child: Row(
                                                mainAxisSize: MainAxisSize.min,
                                                children: [
                                                  Icon(isIll ? Icons.person_off : Icons.event_seat, size: 13, color: c),
                                                  const SizedBox(width: 4),
                                                  Text(
                                                    'Ghế $sName',
                                                    style: TextStyle(
                                                      color: c,
                                                      fontSize: 11,
                                                      fontWeight: FontWeight.bold,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            );
                                          }).toList(),
                                        ),
                                      ),

                                      const SizedBox(height: 10),

                                      // Hàng nút bấm: Xử lý 1 chạm & Xem chi tiết
                                      Padding(
                                        padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                                        child: Row(
                                          children: [
                                            Expanded(
                                              child: ElevatedButton.icon(
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: CSAppColors.danger,
                                                  foregroundColor: Colors.white,
                                                  padding: const EdgeInsets.symmetric(vertical: 10),
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius: BorderRadius.circular(8),
                                                  ),
                                                ),
                                                onPressed: _isBatchResolving
                                                    ? null
                                                    : () => _handleResolveRoom(roomId, showId, roomName, totalRoomAlerts),
                                                icon: const Icon(Icons.check_circle_outline, size: 18),
                                                label: Text(
                                                  'XỬ LÝ TOÀN BỘ PHÒNG ($totalRoomAlerts GHẾ)',
                                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                                ),
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            IconButton(
                                              tooltip: isExpanded ? 'Thu gọn' : 'Xem từng ghế',
                                              style: IconButton.styleFrom(
                                                backgroundColor: CSAppColors.surfaceStrong,
                                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                              ),
                                              icon: Icon(
                                                isExpanded ? Icons.expand_less : Icons.expand_more,
                                                color: CSAppColors.textPrimary,
                                              ),
                                              onPressed: () {
                                                setState(() {
                                                  if (isExpanded) {
                                                    _expandedRooms.remove(groupKey);
                                                  } else {
                                                    _expandedRooms.add(groupKey);
                                                  }
                                                });
                                              },
                                            ),
                                          ],
                                        ),
                                      ),

                                      // Danh sách chi tiết từng ghế khi bấm mở rộng
                                      if (isExpanded)
                                        Container(
                                          padding: const EdgeInsets.fromLTRB(14, 6, 14, 12),
                                          decoration: BoxDecoration(
                                            color: CSAppColors.surfaceStrong,
                                            borderRadius: const BorderRadius.vertical(bottom: Radius.circular(10)),
                                          ),
                                          child: Column(
                                            children: roomAlerts.map((warning) {
                                              final atype = warning['alert_type']?.toString() ?? '';
                                              final color = _color(atype);
                                              final isIll = atype == 'illegal_occupant';
                                              final seat = warning['seat_id'] ?? 'N/A';
                                              final title = isIll
                                                  ? 'Khách ngồi sai ghế / Không có vé'
                                                  : 'Ghế trống bất thường (Đã có vé)';

                                              return Padding(
                                                padding: const EdgeInsets.only(top: 8),
                                                child: InkWell(
                                                  onTap: () async {
                                                    final res = await Navigator.push(
                                                      context,
                                                      MaterialPageRoute(
                                                        builder: (_) => CSWarningDetailScreen(
                                                          alertId: warning['id'] ?? 1,
                                                          alertData: warning,
                                                          onResolved: loadAlerts,
                                                        ),
                                                      ),
                                                    );
                                                    if (res == true) loadAlerts();
                                                  },
                                                  child: Container(
                                                    padding: const EdgeInsets.all(10),
                                                    decoration: BoxDecoration(
                                                      color: CSAppColors.surface,
                                                      borderRadius: BorderRadius.circular(8),
                                                      border: Border.all(color: color.withValues(alpha: 0.5)),
                                                    ),
                                                    child: Row(
                                                      children: [
                                                        Icon(isIll ? Icons.person_off : Icons.event_seat, color: color, size: 20),
                                                        const SizedBox(width: 8),
                                                        Expanded(
                                                          child: Column(
                                                            crossAxisAlignment: CrossAxisAlignment.start,
                                                            children: [
                                                              Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
                                                              Text('Vị trí ghế: $seat', style: TextStyle(fontSize: 11, color: CSAppColors.muted)),
                                                            ],
                                                          ),
                                                        ),
                                                        Icon(Icons.arrow_forward_ios, size: 12, color: CSAppColors.muted),
                                                      ],
                                                    ),
                                                  ),
                                                ),
                                              );
                                            }).toList(),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              );
                            }).toList(),
                          ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricTile({
    required String label,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
      decoration: BoxDecoration(
        color: CSAppColors.surfaceStrong,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 14),
              const SizedBox(width: 4),
              Text(
                value,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w900,
                  fontSize: 15,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(color: CSAppColors.muted, fontSize: 10),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class BoxSideShadow extends BoxShadow {
  const BoxSideShadow({
    super.color = const Color(0x33000000),
    super.offset = Offset.zero,
    super.blurRadius = 0.0,
    super.spreadRadius = 0.0,
  });
}
