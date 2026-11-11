import 'package:flutter/material.dart';

import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'package:mobile_app/core/database/hive_service.dart';
import 'package:mobile_app/core/network/api_client.dart';

class CSOfflineScreen extends StatefulWidget {
  final VoidCallback? onRetry;

  const CSOfflineScreen({
    super.key,
    this.onRetry,
  });

  @override
  State<CSOfflineScreen> createState() => _CSOfflineScreenState();
}

class _CSOfflineScreenState extends State<CSOfflineScreen> {
  bool _isSyncing = false;
  bool _isOnline = true;
  int _pendingCount = 0;
  int _syncedCount = 0;

  @override
  void initState() {
    super.initState();
    _refreshStatus();
  }

  Future<void> _refreshStatus() async {
    final pending = HiveService.getPendingTicketsCount();
    final history = HiveService.getScanHistory();
    final synced = (history.length - pending).clamp(0, history.length);
    setState(() {
      _pendingCount = pending;
      _syncedCount = synced;
    });

    try {
      final rooms = await ApiClient.fetchRooms();
      if (mounted) {
        setState(() {
          _isOnline = rooms.isNotEmpty;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isOnline = false;
        });
      }
    }
  }

  Future<void> _handleSync() async {
    setState(() => _isSyncing = true);
    await ApiClient.syncTicketsToServer('room1', 'all');
    await _refreshStatus();
    if (mounted) {
      setState(() => _isSyncing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _pendingCount == 0
                ? 'Đã đồng bộ toàn bộ dữ liệu vé lên máy chủ!'
                : 'Còn $_pendingCount vé chờ đồng bộ.',
          ),
          backgroundColor: _pendingCount == 0 ? CSAppColors.success : CSAppColors.warning,
        ),
      );
    }
    widget.onRetry?.call();
  }

  @override
  Widget build(BuildContext context) {
    final user = ApiClient.currentUser;
    final staffName = user?['name']?.toString() ?? 'Nhân viên trực ca';
    final shiftLabel = ApiClient.getDynamicShiftLabel(user?['role']?.toString());

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Đồng bộ offline',
              subtitle: 'Quản lý dữ liệu vé lưu cục bộ & đồng bộ máy chủ',
              trailingIcon: Icons.refresh,
              onTrailing: _refreshStatus,
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: [
                  CSOfflineStatusCard(
                    icon: _pendingCount > 0 ? Icons.cloud_upload_outlined : Icons.cloud_done_outlined,
                    title: 'Chờ đồng bộ: $_pendingCount vé',
                    detail: _pendingCount > 0
                        ? 'Dữ liệu soát vé lưu tạm thời trên thiết bị'
                        : 'Không có vé nào đang tồn đọng trên máy',
                    color: _pendingCount > 0 ? CSAppColors.warning : CSAppColors.success,
                    status: _pendingCount > 0 ? 'Đợi' : 'Sạch',
                  ),
                  const SizedBox(height: 10),
                  CSOfflineStatusCard(
                    icon: Icons.sync,
                    title: 'Đã đồng bộ',
                    detail: '$_syncedCount vé đã lưu trữ an toàn trên máy chủ',
                    color: CSAppColors.success,
                    status: 'OK',
                  ),
                  const SizedBox(height: 10),
                  CSAppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'THÔNG TIN CA TRỰC & KẾT NỐI',
                          style: TextStyle(
                            color: CSAppColors.muted,
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.6,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          staffName,
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 15,
                            color: CSAppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          shiftLabel,
                          style: TextStyle(
                            color: CSAppColors.muted,
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Divider(color: CSAppColors.border, height: 1),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                'Trạng thái kết nối máy chủ',
                                style: TextStyle(
                                  color: CSAppColors.muted,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                            Text(
                              _isOnline ? '● Trực tuyến' : '● Ngoại tuyến',
                              style: TextStyle(
                                color: _isOnline ? CSAppColors.success : CSAppColors.danger,
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 96),
              child: CSPrimaryButton(
                label: _isSyncing ? 'Đang đồng bộ...' : 'Đồng bộ ngay bây giờ',
                icon: Icons.sync,
                onPressed: _isSyncing ? null : _handleSync,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CSOfflineStatusCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String detail;
  final Color color;
  final String status;

  const CSOfflineStatusCard({
    super.key,
    required this.icon,
    required this.title,
    required this.detail,
    required this.color,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    return CSAppCard(
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: color.withValues(alpha: .14),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: CSAppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  detail,
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          CSStatusTag(text: status, color: color),
        ],
      ),
    );
  }
}
