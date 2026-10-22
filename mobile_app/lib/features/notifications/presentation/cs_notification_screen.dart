import 'package:flutter/material.dart';


import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'package:mobile_app/core/network/api_client.dart';

/// Hiện popup thông báo nhỏ, bật ra từ góc trên ngay dưới icon chuông.
///
/// [anchorContext] là context của icon chuông — dùng để canh vị trí popup
/// và mũi tên chỉ đúng vào chuông. Nếu null, popup nằm góc trên bên phải.
Future<void> showCSNotificationPopover(
  BuildContext context, {
  BuildContext? anchorContext,
  VoidCallback? onViewAll,
}) {
  Rect? anchor;
  final box = anchorContext?.findRenderObject();
  if (box is RenderBox && box.hasSize) {
    anchor = box.localToGlobal(Offset.zero) & box.size;
  }

  return showGeneralDialog(
    context: context,
    useRootNavigator: true,
    barrierDismissible: true,
    barrierLabel: 'Đóng thông báo',
    barrierColor: Colors.black38,
    transitionDuration: const Duration(milliseconds: 220),
    pageBuilder: (dialogContext, _, _) {
      return _CSNotificationPopover(
        anchor: anchor,
        onViewAll: onViewAll == null
            ? null
            : () {
                Navigator.pop(dialogContext);
                onViewAll();
              },
      );
    },
    transitionBuilder: (context, animation, _, child) {
      final curved = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutBack,
        reverseCurve: Curves.easeIn,
      );
      return FadeTransition(
        opacity: animation,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.85, end: 1).animate(curved),
          alignment: Alignment.topRight,
          child: child,
        ),
      );
    },
  );
}

class _CSNotificationPopover extends StatefulWidget {
  final Rect? anchor;
  final VoidCallback? onViewAll;

  const _CSNotificationPopover({this.anchor, this.onViewAll});

  @override
  State<_CSNotificationPopover> createState() => _CSNotificationPopoverState();
}

class _CSNotificationPopoverState extends State<_CSNotificationPopover> {
  List<dynamic> _alerts = [];
  // state

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final alertsFuture = ApiClient.fetchAlerts();
    final incidentsFuture = ApiClient.getIncidents(limit: 50);

    final results = await Future.wait([alertsFuture, incidentsFuture]);
    final alerts = results[0];
    final incidents = results[1];

    final combined = <dynamic>[...alerts, ...incidents];
    
    // Sort combined list descending
    combined.sort((a, b) {
      final ta = a['timestamp'] ?? a['created_at'] ?? '';
      final tb = b['timestamp'] ?? b['created_at'] ?? '';
      return tb.compareTo(ta);
    });

    if (mounted) {
      setState(() {
        _alerts = combined;
        // loaded
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final anchor = widget.anchor;
    final onViewAll = widget.onViewAll;
    final media = MediaQuery.of(context);
    final screenWidth = media.size.width;
    final panelWidth = (screenWidth - 24).clamp(0.0, 320.0);

    // Vị trí mặc định: góc trên bên phải.
    double top = media.padding.top + 56;
    double right = 12;
    double arrowRight = 22;

    if (anchor != null) {
      top = anchor.bottom + 2;
      right = (screenWidth - anchor.right).clamp(8.0, screenWidth);
      // Mũi tên canh giữa icon chuông.
      arrowRight = (anchor.width / 2 - 7).clamp(12.0, panelWidth - 24);
    }

    return Stack(
      children: [
        Positioned(
          top: top,
          right: right,
          width: panelWidth,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Padding(
                padding: EdgeInsets.only(right: arrowRight),
                child: CustomPaint(
                  size: const Size(14, 8),
                  painter: _ArrowPainter(),
                ),
              ),
              Material(
                color: CSAppColors.surface,
                elevation: 12,
                shadowColor: Colors.black54,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                  side: const BorderSide(color: CSAppColors.primary),
                ),
                clipBehavior: Clip.antiAlias,
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: media.size.height * 0.55,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(14, 8, 4, 0),
                        child: Row(
                          children: [
                            const Text(
                              'Thông báo mới',
                              style: TextStyle(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(width: 7),
                            CSStatusTag(
                              text: '${_alerts.length}',
                              color: CSAppColors.danger,
                            ),
                            const Spacer(),
                            if (onViewAll != null)
                              TextButton(
                                onPressed: onViewAll,
                                child: const Text('Xem tất cả'),
                              ),
                            IconButton(
                              tooltip: 'Đóng',
                              iconSize: 18,
                              onPressed: () => Navigator.pop(context),
                              icon: const Icon(Icons.close),
                            ),
                          ],
                        ),
                      ),
                      Flexible(
                        child: ListView.separated(
                          shrinkWrap: true,
                          padding: const EdgeInsets.fromLTRB(14, 0, 14, 8),
                          itemCount: _alerts.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            return CSNotificationItemView(
                              notification: _alerts[index],
                            );
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ArrowPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, size.height)
      ..lineTo(size.width / 2, 0)
      ..lineTo(size.width, size.height)
      ..close();
    canvas.drawPath(path, Paint()..color = CSAppColors.primary);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Trang danh sách đầy đủ (mở từ "Xem tất cả" hoặc Cài đặt).
/// Không tự vẽ bottom nav — HomeShell đã có thanh nav dùng chung.
class CSNotificationScreen extends StatefulWidget {
  const CSNotificationScreen({super.key});

  @override
  State<CSNotificationScreen> createState() => _CSNotificationScreenState();
}

class _CSNotificationScreenState extends State<CSNotificationScreen> {
  List<dynamic> _alerts = [];
  // state

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final alertsFuture = ApiClient.fetchAlerts();
    final incidentsFuture = ApiClient.getIncidents(limit: 50);

    final results = await Future.wait([alertsFuture, incidentsFuture]);
    final alerts = results[0];
    final incidents = results[1];

    final combined = <dynamic>[...alerts, ...incidents];
    
    // Sort combined list descending
    combined.sort((a, b) {
      final ta = a['timestamp'] ?? a['created_at'] ?? '';
      final tb = b['timestamp'] ?? b['created_at'] ?? '';
      return tb.compareTo(ta);
    });

    if (mounted) {
      setState(() {
        _alerts = combined;
        // loaded
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            const CSScreenHeader(
              title: 'Thông báo',
              subtitle: 'Tất cả thông báo trong ca',
            ),
            CSAppCard(
              child: Column(
                children: [
                  for (var i = 0; i < _alerts.length; i++) ...[
                    if (i > 0) const Divider(),
                    CSNotificationItemView(
                      notification: _alerts[i],
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
}

class CSNotificationItemView extends StatelessWidget {
  final dynamic notification;

  const CSNotificationItemView({
    super.key,
    required this.notification,
  });

  @override
  Widget build(BuildContext context) {
    String title = 'Thông báo hệ thống';
    String detail = '';
    
    // Check if it's an incident vs AI alert
    if (notification.containsKey('category')) {
      // It's an incident
      title = notification['title'] ?? 'Sự cố mới';
      detail = notification['description'] ?? 'Không có mô tả';
    } else {
      // It's an AI alert
      if (notification['alert_type'] == 'damaged_seat') {
        title = 'Báo cáo sự cố ghế';
        detail = 'Ghế ${notification['seat_id']} tại phòng ${notification['room_id']} cần sửa chữa.';
      } else if (notification['alert_type'] == 'over_capacity') {
        title = 'Cảnh báo vượt tải';
        detail = 'Phòng ${notification['room_id']} vượt quá sức chứa.';
      } else if (notification['alert_type'] == 'illegal_occupant') {
        title = 'Khách ngồi sai ghế';
        detail = 'Phát hiện khách ngồi sai ghế tại ${notification['seat_id']}.';
      } else if (notification['alert_type'] == 'missing_guest') {
        title = 'Ghế trống bất thường';
        detail = 'Ghế ${notification['seat_id']} trống nhưng đã có vé.';
      }
    }

    final dateStr = notification['timestamp'] ?? notification['created_at'] ?? '';
    final date = DateTime.tryParse(dateStr)?.toLocal();
    final timeStr = date != null ? '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')} - ${date.day}/${date.month}/${date.year}' : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            detail,
            style: const TextStyle(
              color: CSAppColors.muted,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            timeStr,
            style: const TextStyle(
              color: CSAppColors.muted,
              fontSize: 9,
            ),
          ),
        ],
      ),
    );
  }
}
