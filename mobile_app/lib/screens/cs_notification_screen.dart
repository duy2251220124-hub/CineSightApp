import 'package:flutter/material.dart';

import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_status_tag.dart';

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

class _CSNotificationPopover extends StatelessWidget {
  final Rect? anchor;
  final VoidCallback? onViewAll;

  const _CSNotificationPopover({this.anchor, this.onViewAll});

  @override
  Widget build(BuildContext context) {
    final media = MediaQuery.of(context);
    final screenWidth = media.size.width;
    final panelWidth = (screenWidth - 24).clamp(0.0, 320.0);

    // Vị trí mặc định: góc trên bên phải.
    double top = media.padding.top + 56;
    double right = 12;
    double arrowRight = 22;

    if (anchor != null) {
      top = anchor!.bottom + 2;
      right = (screenWidth - anchor!.right).clamp(8.0, screenWidth);
      // Mũi tên canh giữa icon chuông.
      arrowRight = (anchor!.width / 2 - 7).clamp(12.0, panelWidth - 24);
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
                              text: '${CSMockData.notifications.length}',
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
                          itemCount: CSMockData.notifications.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            return CSNotificationItemView(
                              notification: CSMockData.notifications[index],
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
class CSNotificationScreen extends StatelessWidget {
  const CSNotificationScreen({super.key});

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
                  for (var i = 0; i < CSMockData.notifications.length; i++) ...[
                    if (i > 0) const Divider(),
                    CSNotificationItemView(
                      notification: CSMockData.notifications[i],
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
  final CSMockNotification notification;

  const CSNotificationItemView({
    super.key,
    required this.notification,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            notification.title,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            notification.detail,
            style: const TextStyle(
              color: CSAppColors.muted,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            notification.time,
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
