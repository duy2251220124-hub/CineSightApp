import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';

class CSHomeScreen extends StatefulWidget {
  final Future<void> Function()? onShowtimes;
  final Future<void> Function()? onRooms;
  final Future<void> Function()? onHandover;
  final Future<void> Function(BuildContext)? onNotifications;

  const CSHomeScreen({
    super.key,
    this.onShowtimes,
    this.onRooms,
    this.onHandover,
    this.onNotifications,
  });

  @override
  State<CSHomeScreen> createState() => _CSHomeScreenState();
}

class _CSHomeScreenState extends State<CSHomeScreen> with SingleTickerProviderStateMixin {
  int _activeRooms = 0;
  int _unreadHandoverIncidents = 0; // Chỉ đếm sự cố & bàn giao ca tồn đọng

  late AnimationController _bellAnimController;
  late Animation<double> _bellAnimation;

  @override
  void initState() {
    super.initState();
    _bellAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _bellAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _bellAnimController, curve: Curves.easeInOut),
    );

    _loadData();
  }

  Future<void> _loadData() async {
    final roomsFuture = ApiClient.fetchRooms();
    // Chuông nhỏ trên góc phải: CHỈ lấy sự cố cơ sở vật chất bàn giao ca chưa xử lý
    final incidentsFuture = ApiClient.getIncidents(status: 'open', limit: 50);

    final results = await Future.wait([roomsFuture, incidentsFuture]);
    final rooms = results[0];
    final incidents = results[1];

    final unreadCount = incidents.length;

    if (mounted) {
      setState(() {
        _activeRooms = rooms.length;
        _unreadHandoverIncidents = unreadCount;
      });

      if (_unreadHandoverIncidents > 0) {
        _bellAnimController.repeat(reverse: true);
      } else {
        _bellAnimController.stop();
        _bellAnimController.reset();
      }
    }
  }

  @override
  void dispose() {
    _bellAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadData,
          child: ListView(
            padding: const EdgeInsets.all(14),
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          (ApiClient.currentUser?['name'] ?? 'Nhân viên'),
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                        ),
                        Text(
                          '${(ApiClient.currentUser?['role'] ?? 'Staff')} · ${(ApiClient.currentUser?['id']?.toString() ?? 'NV000')}',
                          style: const TextStyle(
                            color: CSAppColors.muted,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Builder(
                    builder: (bellContext) => Stack(
                      alignment: Alignment.center,
                      clipBehavior: Clip.none,
                      children: [
                        ScaleTransition(
                          scale: _bellAnimation,
                          child: IconButton(
                            tooltip: 'Thông báo sự cố & bàn giao ca',
                            onPressed: widget.onNotifications == null
                                ? null
                                : () async {
                                    await widget.onNotifications!(bellContext);
                                    _loadData();
                                  },
                            icon: Icon(
                              _unreadHandoverIncidents > 0
                                  ? Icons.notifications_active
                                  : Icons.notifications_none,
                              color: _unreadHandoverIncidents > 0 ? CSAppColors.warning : null,
                            ),
                          ),
                        ),
                        if (_unreadHandoverIncidents > 0)
                          Positioned(
                            right: 6,
                            top: 6,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                              decoration: BoxDecoration(
                                color: CSAppColors.warning,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              constraints: const BoxConstraints(
                                minWidth: 16,
                                minHeight: 16,
                              ),
                              child: Text(
                                '$_unreadHandoverIncidents',
                                style: const TextStyle(
                                  color: Colors.black,
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              CSAppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Expanded(
                          child: Text(
                            'CineSight Cinema',
                            style: TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        CSStatusTag(
                          text: '● ON SHIFT',
                          color: CSAppColors.success,
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text('Ca làm việc: ${ApiClient.currentUser?['shift_label'] ?? 'Hôm nay'}'),
                    const SizedBox(height: 5),
                    Text('Rạp đang hoạt động: $_activeRooms phòng'),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  CSHomeAction(
                    icon: Icons.videocam_outlined,
                    label: 'Phòng chiếu',
                    onTap: widget.onRooms == null
                        ? null
                        : () async {
                            await widget.onRooms!();
                            _loadData();
                          },
                  ),
                  CSHomeAction(
                    icon: Icons.calendar_month_outlined,
                    label: 'Suất chiếu',
                    onTap: widget.onShowtimes == null
                        ? null
                        : () async {
                            await widget.onShowtimes!();
                            _loadData();
                          },
                  ),
                  CSHomeAction(
                    icon: Icons.handyman_outlined,
                    label: 'Sự cố & BG',
                    onTap: widget.onHandover == null
                        ? null
                        : () async {
                            await widget.onHandover!();
                            _loadData();
                          },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class CSHomeAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const CSHomeAction({
    super.key,
    required this.icon,
    required this.label,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: CSAppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: CSAppColors.border),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: CSAppColors.primary, size: 24),
                const SizedBox(height: 8),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
