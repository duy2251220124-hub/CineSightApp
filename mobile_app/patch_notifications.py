import re

with open('lib/features/notifications/presentation/cs_notification_screen.dart', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("import 'package:mobile_app/core/widgets/cs_status_tag.dart';", "import 'package:mobile_app/core/widgets/cs_status_tag.dart';\nimport 'package:mobile_app/core/network/api_client.dart';")

# 1. Update _CSNotificationPopover
popover_class_old = """class _CSNotificationPopover extends StatelessWidget {
  final Rect? anchor;
  final VoidCallback? onViewAll;

  const _CSNotificationPopover({this.anchor, this.onViewAll});

  @override
  Widget build(BuildContext context) {"""

popover_class_new = """class _CSNotificationPopover extends StatefulWidget {
  final Rect? anchor;
  final VoidCallback? onViewAll;

  const _CSNotificationPopover({this.anchor, this.onViewAll});

  @override
  State<_CSNotificationPopover> createState() => _CSNotificationPopoverState();
}

class _CSNotificationPopoverState extends State<_CSNotificationPopover> {
  List<dynamic> _alerts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final data = await ApiClient.fetchAlerts();
    if (mounted) {
      setState(() {
        _alerts = data;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final anchor = widget.anchor;
    final onViewAll = widget.onViewAll;"""

content = content.replace(popover_class_old, popover_class_new)

# Popover build adjustments
content = content.replace("text: '${0}',", "text: '${_alerts.length}',")
content = content.replace("itemCount: 0,", "itemCount: _alerts.length,")
content = content.replace("notification: [][index],", "notification: _alerts[index],")


# 2. Update CSNotificationScreen
screen_old = """class CSNotificationScreen extends StatelessWidget {
  const CSNotificationScreen({super.key});

  @override
  Widget build(BuildContext context) {"""

screen_new = """class CSNotificationScreen extends StatefulWidget {
  const CSNotificationScreen({super.key});

  @override
  State<CSNotificationScreen> createState() => _CSNotificationScreenState();
}

class _CSNotificationScreenState extends State<CSNotificationScreen> {
  List<dynamic> _alerts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final data = await ApiClient.fetchAlerts();
    if (mounted) {
      setState(() {
        _alerts = data;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {"""

content = content.replace(screen_old, screen_new)

content = content.replace("for (var i = 0; i < 0; i++)", "for (var i = 0; i < _alerts.length; i++)")
content = content.replace("notification: [][i],", "notification: _alerts[i],")

# 3. Update CSNotificationItemView
item_old = """class CSNotificationItemView extends StatelessWidget {
  final dynamic notification;

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
}"""

item_new = """class CSNotificationItemView extends StatelessWidget {
  final dynamic notification;

  const CSNotificationItemView({
    super.key,
    required this.notification,
  });

  @override
  Widget build(BuildContext context) {
    String title = 'Thông báo hệ thống';
    String detail = '';
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

    final date = DateTime.tryParse(notification['timestamp']?.toString() ?? '');
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
}"""

content = content.replace(item_old, item_new)

with open('lib/features/notifications/presentation/cs_notification_screen.dart', 'w', encoding='utf-8') as f:
    f.write(content)
