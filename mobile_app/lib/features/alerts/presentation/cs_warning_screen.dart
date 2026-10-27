import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
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
                                ? 'CẢNH BÁO TỪ HỆ THỐNG AI (${_alerts.length})'
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
                            style: const TextStyle(color: CSAppColors.muted, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: 'Tải lại',
                      icon: const Icon(Icons.refresh, size: 20),
                      onPressed: () {
                        setState(() => _isLoading = true);
                        loadAlerts();
                      },
                    ),
                  ],
                ),
              ),

              // Danh sách cảnh báo
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _alerts.isEmpty
                        ? ListView(
                            children: const [
                              Padding(
                                padding: EdgeInsets.symmetric(vertical: 80, horizontal: 20),
                                child: Column(
                                  children: [
                                    Icon(Icons.verified_user_outlined, color: CSAppColors.success, size: 54),
                                    SizedBox(height: 12),
                                    Text(
                                      'Không có cảnh báo vi phạm nào!',
                                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                    ),
                                    SizedBox(height: 6),
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
                        : ListView.builder(
                            padding: const EdgeInsets.all(12),
                            itemCount: _alerts.length,
                            itemBuilder: (context, index) {
                              final warning = _alerts[index];
                              final alertType = warning['alert_type']?.toString() ?? '';
                              final color = _color(alertType);

                              final isIllegal = alertType == 'illegal_occupant';
                              final isMissing = alertType == 'missing_guest';

                              final title = isIllegal
                                  ? 'Khách ngồi sai ghế / Không có vé'
                                  : (isMissing
                                      ? 'Ghế trống bất thường (Đã có vé)'
                                      : 'Cảnh báo vượt tải');

                              final seat = warning['seat_id'] ?? warning['seats'] ?? 'N/A';
                              final room = _formatRoomName(warning['room_id']?.toString());
                              final show = warning['show_id']?.toString() ?? '';
                              final timeDisplay = show.contains('T') ? show.split('T')[1] : show;

                              return Padding(
                                padding: const EdgeInsets.only(bottom: 10),
                                child: CSAppCard(
                                  borderColor: color.withValues(alpha: 0.6),
                                  onTap: () async {
                                    if (widget.onWarningSelected != null) {
                                      widget.onWarningSelected!(Map<String, dynamic>.from(warning as Map));
                                      return;
                                    }
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
                                    if (res == true) {
                                      loadAlerts();
                                    }
                                  },
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(8),
                                        decoration: BoxDecoration(
                                          color: color.withValues(alpha: 0.15),
                                          shape: BoxShape.circle,
                                        ),
                                        child: Icon(
                                          isIllegal ? Icons.person_off : Icons.event_seat_outlined,
                                          color: color,
                                          size: 20,
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Row(
                                              children: [
                                                Expanded(
                                                  child: Text(
                                                    title,
                                                    style: TextStyle(
                                                      fontWeight: FontWeight.bold,
                                                      fontSize: 13,
                                                      color: color,
                                                    ),
                                                  ),
                                                ),
                                                CSStatusTag(
                                                  text: 'GHẾ $seat',
                                                  color: color,
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 5),
                                            Text(
                                              '$room · Suất $timeDisplay',
                                              style: const TextStyle(
                                                color: Colors.white,
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              isIllegal
                                                  ? '👉 Có người ngồi thực tế nhưng chưa soát vé.'
                                                  : '👉 Đã soát vé tại cửa nhưng ghế đang trống.',
                                              style: const TextStyle(
                                                color: CSAppColors.muted,
                                                fontSize: 11,
                                              ),
                                            ),
                                            const SizedBox(height: 8),
                                            Row(
                                              children: [
                                                Text(
                                                  'Chạm để xử lý vi phạm',
                                                  style: TextStyle(
                                                    color: color,
                                                    fontSize: 11,
                                                    fontWeight: FontWeight.w700,
                                                  ),
                                                ),
                                                Icon(Icons.arrow_forward_ios, color: color, size: 10),
                                              ],
                                            ),
                                          ],
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
      ),
    );
  }
}
