import 'package:flutter/material.dart';

import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/features/alerts/presentation/cs_handover_screen.dart';

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
                            Text(
                              'Bàn giao ca & Sự cố',
                              style: TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 13,
                                color: CSAppColors.textPrimary,
                              ),
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
                              icon: Icon(Icons.close, color: CSAppColors.textPrimary),
                            ),
                          ],
                        ),
                      ),
                      Divider(height: 1, color: CSAppColors.border),
                      Flexible(
                        child: _isLoading
                            ? const Padding(
                                padding: EdgeInsets.all(20),
                                child: Center(child: CircularProgressIndicator()),
                              )
                            : _incidents.isEmpty
                                ? Padding(
                                    padding: const EdgeInsets.all(20),
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
                                    separatorBuilder: (_, _) => Divider(height: 1, color: CSAppColors.border),
                                    itemBuilder: (context, index) {
                                      return CSHandoverIncidentItemView(
                                        incident: _incidents[index],
                                        onResolved: _loadData,
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
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
            children: [
              const CSScreenHeader(
                title: 'Bàn giao ca & Sự cố',
                subtitle: 'Chạm vào sự cố để mở khung xem chi tiết',
              ),
              if (_isLoading)
                const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_incidents.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(40),
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
                        if (i > 0) Divider(color: CSAppColors.border),
                        CSHandoverIncidentItemView(
                          incident: _incidents[i],
                          onResolved: _loadData,
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
  final VoidCallback? onResolved;

  const CSHandoverIncidentItemView({
    super.key,
    required this.incident,
    this.onResolved,
  });

  @override
  Widget build(BuildContext context) {
    final title = incident['title'] ?? 'Sự cố phòng chiếu';
    final desc = incident['description'] ?? 'Không có mô tả chi tiết';
    final rawRoom = incident['room_id'] ?? incident['room'] ?? '';
    final room = formatRoomName(rawRoom.toString());
    final rawSeats = incident['seat_ids'] ?? incident['seat_id'] ?? incident['seats'];
    String seats = '';
    if (rawSeats is List && rawSeats.isNotEmpty) {
      seats = rawSeats.join(', ');
    } else if (rawSeats != null && rawSeats.toString().trim().isNotEmpty && rawSeats.toString() != '[]') {
      seats = rawSeats.toString();
    }
    final reporter = incident['reporter_name'] ?? incident['created_by'] ?? 'Nhân viên ca trước';
    final shiftLabel = incident['shift_label'] ?? incident['reporter_shift'] ?? '';

    final dateStr = incident['created_at'] ?? incident['timestamp'] ?? '';
    final date = DateTime.tryParse(dateStr)?.toLocal();
    final timeStr = date != null
        ? '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')} · ${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}'
        : '';

    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => showIncidentDetailDialog(
        context,
        incident,
        onResolved: onResolved,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
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
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 14,
                            color: CSAppColors.textPrimary,
                          ),
                        ),
                      ),
                      const CSStatusTag(text: 'CHỜ XỬ LÝ', color: CSAppColors.warning),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: CSAppColors.surfaceStrong,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: CSAppColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (room.isNotEmpty || seats.isNotEmpty)
                          Row(
                            children: [
                              const Icon(Icons.meeting_room_rounded, size: 14, color: CSAppColors.primary),
                              const SizedBox(width: 5),
                              Expanded(
                                child: Text(
                                  '${rawRoom.toString().isNotEmpty ? room : ''}${seats.isNotEmpty ? ' · Ghế $seats' : ''}',
                                  style: TextStyle(
                                    color: CSAppColors.textPrimary,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            const Icon(Icons.person_pin_rounded, size: 14, color: CSAppColors.success),
                            const SizedBox(width: 5),
                            Expanded(
                              child: Text(
                                'Người báo: $reporter${shiftLabel.toString().isNotEmpty ? ' ($shiftLabel)' : ''}',
                                style: TextStyle(
                                  color: CSAppColors.textPrimary,
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (timeStr.isNotEmpty) ...[
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              const Icon(Icons.access_time_filled_rounded, size: 14, color: CSAppColors.warning),
                              const SizedBox(width: 5),
                              Expanded(
                                child: Text(
                                  'Giờ báo: $timeStr',
                                  style: const TextStyle(color: CSAppColors.warning, fontSize: 11.5, fontWeight: FontWeight.w700),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    desc,
                    style: TextStyle(color: CSAppColors.textSecondary, fontSize: 11.5),
                  ),
                  if (incident['image_path'] != null && incident['image_path'].toString().trim().isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Builder(
                      builder: (ctx) {
                        final imgUrl = ApiClient.getImageUrl(incident['image_path'].toString());
                        return ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: InkWell(
                            onTap: () {
                              showDialog(
                                context: ctx,
                                builder: (dialogCtx) => Dialog(
                                  backgroundColor: Colors.transparent,
                                  insetPadding: const EdgeInsets.all(12),
                                  child: Stack(
                                    alignment: Alignment.topRight,
                                    children: [
                                      InteractiveViewer(
                                        child: Image.network(
                                          imgUrl,
                                          headers: const {'ngrok-skip-browser-warning': 'true'},
                                          fit: BoxFit.contain,
                                          errorBuilder: (_, _, _) => Container(
                                            padding: const EdgeInsets.all(20),
                                            color: Colors.black87,
                                            child: const Text('Không thể tải ảnh hiện trường', style: TextStyle(color: Colors.white70)),
                                          ),
                                        ),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.close, color: Colors.white, size: 28),
                                        onPressed: () => Navigator.of(dialogCtx).pop(),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                            child: Stack(
                              alignment: Alignment.bottomRight,
                              children: [
                                Image.network(
                                  imgUrl,
                                  height: 120,
                                  width: double.infinity,
                                  fit: BoxFit.cover,
                                  headers: const {'ngrok-skip-browser-warning': 'true'},
                                  errorBuilder: (_, _, _) => Container(
                                    height: 60,
                                    color: CSAppColors.surfaceStrong,
                                    alignment: Alignment.center,
                                    child: Text('Lỗi tải ảnh', style: TextStyle(color: CSAppColors.muted, fontSize: 11)),
                                  ),
                                ),
                                Container(
                                  margin: const EdgeInsets.all(6),
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withValues(alpha: 0.7),
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.zoom_in, color: Colors.white, size: 12),
                                      SizedBox(width: 4),
                                      Text('Xem ảnh', style: TextStyle(color: Colors.white, fontSize: 10)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                  const SizedBox(height: 5),
                  const Row(
                    children: [
                      Icon(Icons.touch_app_outlined, size: 12, color: CSAppColors.primary),
                      SizedBox(width: 4),
                      Text(
                        'Chạm để mở chi tiết sự cố',
                        style: TextStyle(color: CSAppColors.primary, fontSize: 10.5, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
