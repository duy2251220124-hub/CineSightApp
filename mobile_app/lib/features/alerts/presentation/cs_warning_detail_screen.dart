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

  Future<void> _submitResolution(String resolution) async {
    final alert = widget.alertData ?? {};
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() => _isResolving = true);
    final roomId = alert['room_id']?.toString();
    final showId = alert['show_id']?.toString();
    bool success = await ApiClient.resolveAlert(
      widget.alertId,
      resolution: resolution,
    );
    if (!success &&
        roomId != null &&
        showId != null &&
        roomId.isNotEmpty &&
        showId.isNotEmpty) {
      success = await ApiClient.resolveRoomAlerts(
        roomId,
        showId,
        resolution: resolution,
      );
    }
    if (!mounted) return;
    setState(() => _isResolving = false);
    if (success) {
      final msg = resolution == 'ticket_verified'
          ? 'Đã xác nhận khách có vé hợp lệ & bổ sung ghế vào Tập A!'
          : 'Đã đánh dấu xử lý vi phạm thành công!';
      messenger.showSnackBar(
        SnackBar(
          content: Text(msg),
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
  }

  @override
  Widget build(BuildContext context) {
    final alert = widget.alertData ?? {};
    final type = alert['alert_type']?.toString() ?? 'illegal_occupant';
    final isHopping = alert['suspected_type'] == 'vip_seat_hopping';
    final isDup = type == 'duplicate_scan';
    final isForged = type == 'forged_ticket';
    final isIllegal = type == 'illegal_occupant' || isDup || isForged;
    final isMissing = type == 'missing_guest';
    final color = isIllegal ? CSAppColors.danger : (isMissing ? CSAppColors.warning : CSAppColors.primary);

    final title = isHopping
        ? 'Nghi vấn tự ý nâng hạng ghế VIP (VIP Seat Hopping)'
        : isDup
            ? 'Gian lận quét trùng vé đa thiết bị'
            : isForged
                ? 'Phát hiện vé giả mạo chữ ký số'
                : isIllegal
                    ? 'Khách ngồi sai ghế / Không vé'
                    : (isMissing ? 'Ghế trống bất thường (Vắng khách)' : 'Cảnh báo vượt tải');
    
    final desc = isHopping
        ? (alert['hopping_message']?.toString() ??
            'Hệ thống phát hiện ghế VIP đang có người ngồi chưa soát vé đồng thời có ghế Thường đã soát vé nhưng để trống.')
        : isDup
            ? (alert['detail']?.toString() ??
                'Phát hiện vé cho vị trí ghế này được quét trùng trên nhiều thiết bị khi đồng bộ Offline.')
            : isForged
                ? (alert['detail']?.toString() ??
                    'Mã QR vé không khớp chữ ký số HMAC-SHA256 của hệ thống.')
                : isIllegal
                    ? 'Hệ thống AI camera phát hiện có người ngồi tại vị trí ghế này nhưng không có dữ liệu vé hợp lệ đã soát tại cửa.'
                    : (isMissing
                        ? 'Vé cho ghế này đã được nhân viên soát hợp lệ tại cửa, nhưng camera AI ghi nhận thực tế ghế đang để trống.'
                        : 'Tổng số người thực tế trong phòng vượt quá số lượng ghế quy định.');

    final seat = alert['seat_id'] ?? alert['seats'] ?? 'N/A';
    final tier = alert['seat_tier']?.toString() ?? ApiClient.getSeatTier('$seat');
    final room = _formatRoom(alert['room_id']?.toString());
    final show = alert['show_id']?.toString() ?? 'N/A';

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chi tiết cảnh báo AI',
              subtitle: 'Kiểm tra hiện trường phòng chiếu',
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 125),
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
                                style: TextStyle(color: CSAppColors.muted, fontSize: 11),
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
                        Text(
                          'THÔNG TIN VI PHẠM',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.1,
                            color: CSAppColors.muted,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _buildRow(
                          'Vị trí ghế vi phạm:',
                          '$seat (${tier == "VIP" ? "Ghế VIP" : "Ghế Thường"})',
                          isBold: true,
                          highlightColor: color,
                        ),
                        if (isHopping) ...[
                          const Divider(height: 18),
                          _buildRow(
                            'Đối chiếu nâng hạng:',
                            'Từ ghế Thường ${alert["hopping_from"]} ➔ VIP $seat',
                            highlightColor: const Color(0xFFD97706),
                          ),
                        ],
                        const Divider(height: 18),
                        _buildRow('Số vé đã quét:', '${alert['scanned_tickets_count'] ?? 'N/A'} vé'),
                        const Divider(height: 18),
                        _buildRow('Số người hiện có trong rạp:', '${alert['detected_people_count'] ?? 'N/A'} người'),
                        const Divider(height: 18),
                        _buildRow('Ghế cảnh báo cùng đợt:', '${(alert['all_alerted_seats'] as List?)?.join(', ') ?? seat}'),
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
                        Text(
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
                          style: TextStyle(
                            fontSize: 12,
                            height: 1.4,
                            color: CSAppColors.textPrimary,
                          ),
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
                  const SizedBox(height: 18),
                  CSPrimaryButton(
                    label: _isResolving
                        ? 'Đang cập nhật...'
                        : '1. Đã xử lý vi phạm (Yêu cầu về đúng ghế)',
                    icon: Icons.check_circle_outline,
                    onPressed: _isResolving
                        ? null
                        : () => _submitResolution('violation_handled'),
                  ),
                  if (isIllegal && !isForged) ...[
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: CSAppColors.success,
                          side: const BorderSide(color: CSAppColors.success, width: 1.4),
                          padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        onPressed: _isResolving
                            ? null
                            : () => _submitResolution('ticket_verified'),
                        icon: const Icon(Icons.verified_outlined, size: 18),
                        label: const Text(
                          '2. Khách có vé hợp lệ bị sót quét (Bổ sung Tập A)',
                          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5),
                        ),
                      ),
                    ),
                  ],
                ],
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
        Text(label, style: TextStyle(color: CSAppColors.muted, fontSize: 13)),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: TextStyle(
              fontWeight: isBold ? FontWeight.bold : FontWeight.w600,
              color: highlightColor ?? CSAppColors.textPrimary,
              fontSize: isBold ? 15 : 13,
            ),
          ),
        ),
      ],
    );
  }
}
