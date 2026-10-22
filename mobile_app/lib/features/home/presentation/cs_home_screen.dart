import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';

class CSHomeScreen extends StatefulWidget {
  final Future<void> Function(BuildContext)? onNotifications;
  final Future<void> Function()? onShowtimes;
  final Future<void> Function()? onRooms;
  final Future<void> Function()? onHandover;

  const CSHomeScreen({
    super.key,
    this.onNotifications,
    this.onShowtimes,
    this.onRooms,
    this.onHandover,
  });

  @override
  State<CSHomeScreen> createState() => _CSHomeScreenState();
}

class _CSHomeScreenState extends State<CSHomeScreen> with SingleTickerProviderStateMixin {
  int _activeRooms = 0;
  int _unreadNotifications = 0;
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
    final rooms = await ApiClient.fetchRooms();
    
    // Check notifications
    final alertsFuture = ApiClient.fetchAlerts();
    final incidentsFuture = ApiClient.getIncidents(status: 'open', limit: 50);

    final results = await Future.wait([alertsFuture, incidentsFuture]);
    final alerts = results[0] as List<dynamic>;
    final incidents = results[1] as List<dynamic>;

    final unreadCount = alerts.length + incidents.length;

    if (mounted) {
      setState(() { 
        _activeRooms = rooms.length; 
        _unreadNotifications = unreadCount;
      });

      if (_unreadNotifications > 0) {
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
                        style: const TextStyle(fontWeight: FontWeight.w700),
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
                    children: [
                      ScaleTransition(
                        scale: _bellAnimation,
                        child: IconButton(
                          onPressed: widget.onNotifications == null
                              ? null
                              : () async {
                                  await widget.onNotifications!(bellContext);
                                  _loadData();
                                },
                          icon: Icon(
                            _unreadNotifications > 0 ? Icons.notifications_active : Icons.notifications_none,
                            color: _unreadNotifications > 0 ? CSAppColors.danger : null,
                          ),
                        ),
                      ),
                      if (_unreadNotifications > 0)
                        Positioned(
                          right: 8,
                          top: 8,
                          child: Container(
                            padding: const EdgeInsets.all(2),
                            decoration: const BoxDecoration(
                              color: Colors.red,
                              shape: BoxShape.circle,
                            ),
                            constraints: const BoxConstraints(
                              minWidth: 14,
                              minHeight: 14,
                            ),
                            child: Text(
                              '$_unreadNotifications',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 8,
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
                  const Text('Ca làm việc: Hôm nay'),
                  const SizedBox(height: 5),
                  Text('Rạp đang hoạt động: $_activeRooms'),
                ],
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                CSHomeAction(
                  icon: Icons.calendar_month_outlined,
                  label: 'Suất chiếu',
                  onTap: widget.onShowtimes == null ? null : () async {
                    await widget.onShowtimes!();
                    _loadData();
                  },
                ),
                CSHomeAction(
                  icon: Icons.videocam_outlined,
                  label: 'Phòng chiếu',
                  onTap: widget.onRooms == null ? null : () async {
                    await widget.onRooms!();
                    _loadData();
                  },
                ),
                CSHomeAction(
                  icon: Icons.handyman_outlined,
                  label: 'Sự cố & BG',
                  onTap: widget.onHandover == null ? null : () async {
                    await widget.onHandover!();
                    _loadData();
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class CSHomeAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final Future<void> Function()? onTap;

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
        child: CSAppCard(
          onTap: onTap,
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Column(
            children: [
              Icon(icon, color: CSAppColors.primary, size: 30),
              const SizedBox(height: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
