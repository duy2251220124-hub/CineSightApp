import 'package:flutter/material.dart';

import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'package:mobile_app/core/network/api_client.dart';

/// Hiện popup thông báo Bàn giao ca & Sự cố rạp nhỏ, bật ra từ icon chuông góc trên bên phải.
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
  List<dynamic> _incidents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    // Chỉ tải danh sách sự cố & bàn giao ca chưa xử lý
    final incidents = await ApiClient.getIncidents(status: 'open', limit: 50);

    // Sort descending by created_at
    incidents.sort((a, b) {
      final ta = a['created_at'] ?? a['timestamp'] ?? '';
      final tb = b['created_at'] ?? b['timestamp'] ?? '';
      return tb.compareTo(ta);
    });

    if (mounted) {
      setState(() {
        _incidents = incidents;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final anchor = widget.anchor;
    final onViewAll = widget.onViewAll;
    final media = MediaQuery.of(context);
    final screenWidth = media.size.width;
    final panelWidth = (screenWidth - 24).clamp(0.0, 340.0);

    double top = media.padding.top + 56;
    double right = 12;
    double arrowRight = 22;

    if (anchor != null) {
      top = anchor.bottom + 2;
      right = (screenWidth - anchor.right).clamp(8.0, screenWidth);
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
                        padding: const EdgeInsets.fromLTRB(14, 10, 4, 4),
                        child: Row(
                          children: [
                            const Text(
                              'Bàn giao ca & Sự cố',
                              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                            ),
                            const SizedBox(width: 7),
                            CSStatusTag(
                              text: '${_incidents.length}',
                              color: CSAppColors.warning,
                            ),
                            const Spacer(),
                            if (onViewAll != null)
                              TextButton(
                                onPressed: onViewAll,
                                child: const Text('Xem tất cả', style: TextStyle(fontSize: 11)),
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
                      const Divider(height: 1),
                      Flexible(
                        child: _isLoading
                            ? const Padding(
                                padding: EdgeInsets.all(20),
                                child: Center(child: CircularProgressIndicator()),
                              )
                            : _incidents.isEmpty
                                ? const Padding(
                                    padding: EdgeInsets.all(20),
                                    child: Center(
                                      child: Text(
                                        'Không có sự cố nào tồn đọng từ ca trước',
                                        style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                                        textAlign: TextAlign.center,
                                      ),
                                    ),
                                  )
                                : ListView.separated(
                                    shrinkWrap: true,
                                    padding: const EdgeInsets.fromLTRB(14, 6, 14, 8),
                                    itemCount: _incidents.length,
                                    separatorBuilder: (_, _) => const Divider(height: 1),
                                    itemBuilder: (context, index) {
                                      return CSHandoverIncidentItemView(
                                        incident: _incidents[index],
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

/// Màn hình danh sách sự cố bàn giao ca đầy đủ
class CSNotificationScreen extends StatefulWidget {
  const CSNotificationScreen({super.key});

  @override
  State<CSNotificationScreen> createState() => _CSNotificationScreenState();
}

class _CSNotificationScreenState extends State<CSNotificationScreen> {
  List<dynamic> _incidents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final incidents = await ApiClient.getIncidents(status: 'open', limit: 50);

    incidents.sort((a, b) {
      final ta = a['created_at'] ?? a['timestamp'] ?? '';
      final tb = b['created_at'] ?? b['timestamp'] ?? '';
      return tb.compareTo(ta);
    });

    if (mounted) {
      setState(() {
        _incidents = incidents;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            children: [
              const CSScreenHeader(
                title: 'Bàn giao ca & Sự cố',
                subtitle: 'Các sự cố, trục trặc cơ sở vật chất từ ca trước',
              ),
              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_incidents.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(
                    child: Text(
                      'Tất cả sự cố đã được giải quyết!\nKhông có ghi chú bàn giao tồn đọng.',
                      style: TextStyle(color: CSAppColors.muted),
                      textAlign: TextAlign.center,
                    ),
                  ),
                )
              else
                CSAppCard(
                  child: Column(
                    children: [
                      for (var i = 0; i < _incidents.length; i++) ...[
                        if (i > 0) const Divider(),
                        CSHandoverIncidentItemView(
                          incident: _incidents[i],
                        ),
                      ],
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class CSHandoverIncidentItemView extends StatelessWidget {
  final dynamic incident;

  const CSHandoverIncidentItemView({
    super.key,
    required this.incident,
  });

  @override
  Widget build(BuildContext context) {
    final title = incident['title'] ?? 'Sự cố phòng chiếu';
    final desc = incident['description'] ?? 'Không có mô tả chi tiết';
    final rawRoom = incident['room_id'] ?? incident['room'] ?? '';
    final room = formatRoomName(rawRoom.toString());
    final seats = incident['seat_id'] ?? incident['seats'] ?? '';
    final reporter = incident['reporter_name'] ?? incident['created_by'] ?? 'Nhân viên ca trước';

    final dateStr = incident['created_at'] ?? incident['timestamp'] ?? '';
    final date = DateTime.tryParse(dateStr)?.toLocal();
    final timeStr = date != null
        ? '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')} · ${date.day}/${date.month}/${date.year}'
        : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: CSAppColors.warning.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.handyman_outlined, color: CSAppColors.warning, size: 18),
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
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ),
                    const CSStatusTag(text: 'CHỜ XỬ LÝ', color: CSAppColors.warning),
                  ],
                ),
                const SizedBox(height: 4),
                if (room.isNotEmpty || seats.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 3),
                    child: Text(
                      'Vị trí: ${rawRoom.toString().isNotEmpty ? room : ''}${seats.isNotEmpty ? ' · Ghế $seats' : ''}',
                      style: const TextStyle(color: CSAppColors.primary, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ),
                Text(
                  desc,
                  style: const TextStyle(color: CSAppColors.muted, fontSize: 11),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      'Bàn giao bởi: $reporter',
                      style: const TextStyle(color: CSAppColors.muted, fontSize: 10, fontStyle: FontStyle.italic),
                    ),
                    const Spacer(),
                    Text(
                      timeStr,
                      style: const TextStyle(color: CSAppColors.muted, fontSize: 9),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
