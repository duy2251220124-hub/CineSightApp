import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';

class CSWarningDetailScreen extends StatefulWidget {
  final VoidCallback? onResolved;
  final int alertId;
  final Map<String, dynamic>? alertData;

  const CSWarningDetailScreen({
    super.key,
    this.onResolved,
    required this.alertId,
    this.alertData,
  });

  @override
  State<CSWarningDetailScreen> createState() => _CSWarningDetailScreenState();
}

class _CSWarningDetailScreenState extends State<CSWarningDetailScreen> {
  bool _isResolving = false;

  String _formatRoom(String? r) => formatRoomName(r);

  @override
  Widget build(BuildContext context) {
    final alert = widget.alertData ?? {};
    final type = alert['alert_type']?.toString() ?? 'illegal_occupant';
    final isIllegal = type == 'illegal_occupant';
    final isMissing = type == 'missing_guest';
    final color = isIllegal ? CSAppColors.danger : (isMissing ? CSAppColors.warning : CSAppColors.primary);

    final title = isIllegal
        ? 'Khách ngồi sai ghế / Không vé'
        : (isMissing ? 'Ghế trống bất thường (Vắng khách)' : 'Cảnh báo vượt tải');
    
    final desc = isIllegal
        ? 'Hệ thống AI camera phát hiện có người ngồi tại vị trí ghế này nhưng không có dữ liệu vé hợp lệ đã soát tại cửa.'
        : (isMissing
            ? 'Vé cho ghế này đã được nhân viên soát hợp lệ tại cửa, nhưng camera AI ghi nhận thực tế ghế đang để trống.'
            : 'Tổng số người thực tế trong phòng vượt quá số lượng ghế quy định.');

    final seat = alert['seat_id'] ?? alert['seats'] ?? 'N/A';
    final room = _formatRoom(alert['room_id']?.toString());
    final show = alert['show_id']?.toString() ?? 'N/A';

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chi tiết cảnh báo AI',
              subtitle: 'Kiểm tra hiện trường phòng chiếu',
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: [
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: color, width: 1.5),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.warning_rounded, color: color, size: 36),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                title.toUpperCase(),
                                style: TextStyle(
                                  color: color,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 3),
                              Text(
                                'Mã cảnh báo: #${widget.alertId}',
                                style: const TextStyle(color: CSAppColors.muted, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
                  CSAppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'THÔNG TIN VI PHẠM',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.1,
                            color: CSAppColors.muted,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _buildRow('Vị trí ghế vi phạm:', '$seat', isBold: true, highlightColor: color),
                        const Divider(height: 18),
                        _buildRow('Phòng chiếu:', room),
                        const Divider(height: 18),
                        _buildRow('Suất chiếu:', show),
                        const Divider(height: 18),
                        _buildRow('Trạng thái:', 'Chưa giải quyết', highlightColor: CSAppColors.danger),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
                  CSAppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'HƯỚNG DẪN XỬ LÝ',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.1,
                            color: CSAppColors.muted,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          desc,
                          style: const TextStyle(fontSize: 12, height: 1.4),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          isIllegal
                              ? '👉 Nhân viên vào phòng chiếu kiểm tra vị trí ghế $seat, nhắc nhở khách về đúng ghế hoặc mời khách ra quầy mua bổ sung vé.'
                              : '👉 Nhân viên kiểm tra xem khách có đang đi vệ sinh hoặc đổi sang ghế khác trong rạp hay không.',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: CSAppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                color: CSAppColors.surface,
                border: Border(top: BorderSide(color: CSAppColors.border)),
              ),
              child: CSPrimaryButton(
                label: _isResolving ? 'Đang cập nhật...' : 'Xác nhận đã xử lý vi phạm',
                icon: Icons.check_circle_outline,
                onPressed: _isResolving
                    ? null
                    : () async {
                        final messenger = ScaffoldMessenger.of(context);
                        final navigator = Navigator.of(context);
                        setState(() => _isResolving = true);
                        final success = await ApiClient.resolveAlert(widget.alertId);
                        if (!mounted) return;
                        setState(() => _isResolving = false);
                        if (success) {
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Đã đánh dấu xử lý vi phạm thành công!'),
                              backgroundColor: CSAppColors.success,
                            ),
                          );
                          widget.onResolved?.call();
                          navigator.pop(true);
                        } else {
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Không thể cập nhật, vui lòng thử lại!'),
                              backgroundColor: CSAppColors.danger,
                            ),
                          );
                        }
                      },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value, {bool isBold = false, Color? highlightColor}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: CSAppColors.muted, fontSize: 13)),
        Text(
          value,
          style: TextStyle(
            fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            color: highlightColor ?? Colors.white,
            fontSize: isBold ? 15 : 13,
          ),
        ),
      ],
    );
  }
}
