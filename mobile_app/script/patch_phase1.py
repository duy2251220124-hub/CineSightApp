import os

home_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';

class CSHomeScreen extends StatefulWidget {
  final ValueChanged<BuildContext>? onNotifications;
  final VoidCallback? onShowtimes;
  final VoidCallback? onRooms;
  final VoidCallback? onHandover;

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

class _CSHomeScreenState extends State<CSHomeScreen> {
  int _activeRooms = 0;
  
  @override
  void initState() {
    super.initState();
    ApiClient.fetchRooms().then((rooms) {
      if (mounted) setState(() { _activeRooms = rooms.length; });
    });
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
                  builder: (bellContext) => IconButton(
                    onPressed: widget.onNotifications == null
                        ? null
                        : () => widget.onNotifications!(bellContext),
                    icon: const Icon(Icons.notifications_none),
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
                  onTap: widget.onShowtimes,
                ),
                CSHomeAction(
                  icon: Icons.videocam_outlined,
                  label: 'Phòng chiếu',
                  onTap: widget.onRooms,
                ),
                CSHomeAction(
                  icon: Icons.handyman_outlined,
                  label: 'Sự cố & BG',
                  onTap: widget.onHandover,
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
"""

rooms_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSRoomsScreen extends StatefulWidget {
  final ValueChanged<Map<String, dynamic>>? onConfirmed;

  const CSRoomsScreen({super.key, this.onConfirmed});

  @override
  State<CSRoomsScreen> createState() => _CSRoomsScreenState();
}

class _CSRoomsScreenState extends State<CSRoomsScreen> {
  int _selectedIndex = -1;
  List<dynamic> _rooms = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRooms();
  }

  Future<void> _loadRooms() async {
    final rooms = await ApiClient.fetchRooms();
    if (mounted) {
      setState(() {
        _rooms = rooms;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chọn phòng chiếu',
              subtitle: 'Hôm nay',
              trailingIcon: Icons.notifications_none,
            ),
            Expanded(
              child: _isLoading 
                ? const Center(child: CircularProgressIndicator()) 
                : ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                itemCount: _rooms.length,
                itemBuilder: (context, index) {
                  final room = _rooms[index];
                  final roomId = room['room_id'] ?? 'Unknown';
                  final seats = room['total_seats'] ?? 0;
                  final status = room['is_calibrated'] == true ? 'Đã hiệu chuẩn' : 'Chưa hiệu chuẩn';

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 9),
                    child: CSAppCard(
                      borderColor: _selectedIndex == index
                          ? CSAppColors.primary
                          : CSAppColors.border,
                      onTap: () => setState(() => _selectedIndex = index),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  roomId,
                                  style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                Text(
                                  'Tổng số ghế: $seats',
                                  style: const TextStyle(
                                    color: CSAppColors.muted,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Text(
                            '● $status',
                            style: TextStyle(
                              color: room['is_calibrated'] == true ? CSAppColors.success : CSAppColors.warning,
                              fontSize: 10,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: CSPrimaryButton(
                label: 'Xác nhận phòng chiếu',
                onPressed: _selectedIndex == -1 ? null : () {
                  widget.onConfirmed?.call(_rooms[_selectedIndex]);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

showtimes_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSShowtimesScreen extends StatelessWidget {
  final ValueChanged<Map<String, dynamic>>? onMovieSelected;

  const CSShowtimesScreen({
    super.key,
    this.onMovieSelected,
  });

  @override
  Widget build(BuildContext context) {
    // API chưa cung cấp danh sách suất chiếu, nên tạo 1 suất cứng để test
    final mockShowtime = {
      'id': '2026-09-25T19:30',
      'movie_name': 'Suất chiếu mẫu',
      'time': '19:30',
    };

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chọn suất chiếu',
              subtitle: 'Hôm nay',
              trailingIcon: Icons.notifications_none,
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: TextField(
                decoration: InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  hintText: 'Tên phim',
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: CSAppCard(
                      onTap: () => onMovieSelected?.call(mockShowtime),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(mockShowtime['movie_name']!, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          Text('Mã suất chiếu: ${mockShowtime['id']}', style: const TextStyle(color: CSAppColors.muted)),
                        ]
                      )
                    )
                  )
                ]
              )
            ),
          ],
        ),
      ),
    );
  }
}
"""

with open('lib/features/home/presentation/cs_home_screen.dart', 'w', encoding='utf-8') as f:
    f.write(home_screen_content)

with open('lib/features/rooms/presentation/cs_rooms_screen.dart', 'w', encoding='utf-8') as f:
    f.write(rooms_screen_content)

with open('lib/features/rooms/presentation/cs_showtimes_screen.dart', 'w', encoding='utf-8') as f:
    f.write(showtimes_screen_content)
