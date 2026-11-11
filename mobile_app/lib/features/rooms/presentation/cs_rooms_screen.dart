import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
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

  static const List<Map<String, dynamic>> _fallbackRooms = [
    {'room_id': 'room1', 'name': 'Phòng chiếu số 1', 'total_seats': 136, 'is_calibrated': true},
    {'room_id': 'room2', 'name': 'Phòng chiếu số 2', 'total_seats': 136, 'is_calibrated': true},
    {'room_id': 'room3', 'name': 'Phòng chiếu số 3', 'total_seats': 132, 'is_calibrated': true},
    {'room_id': 'room4', 'name': 'Phòng chiếu số 4', 'total_seats': 136, 'is_calibrated': true},
  ];

  Future<void> _loadRooms() async {
    setState(() => _isLoading = true);
    final rooms = await ApiClient.fetchRooms();
    if (mounted) {
      setState(() {
        _rooms = rooms.isNotEmpty ? rooms : _fallbackRooms;
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
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Chọn phòng chiếu',
              subtitle: 'Chạm vào phòng chiếu để xem sơ đồ ghế trực tiếp',
              trailingIcon: Icons.refresh,
              onTrailing: _loadRooms,
            ),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(12, 4, 12, 125),
                      itemCount: _rooms.length,
                      itemBuilder: (context, index) {
                        final room = _rooms[index];
                        final rawRoomId = (room['room_id'] ?? 'room1').toString();
                        final roomName = formatRoomName(room['name']?.toString() ?? rawRoomId);
                        final seats = room['total_seats'] ?? (rawRoomId.contains('3') ? 132 : 136);
                        final isCalibrated = room['is_calibrated'] == true;
                        final status = isCalibrated ? 'Đã hiệu chuẩn' : 'Chưa hiệu chuẩn';

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: CSAppCard(
                            borderColor: _selectedIndex == index
                                ? CSAppColors.primary
                                : CSAppColors.border,
                            onTap: () {
                              setState(() => _selectedIndex = index);
                              widget.onConfirmed?.call(_rooms[index]);
                            },
                            child: Row(
                              children: [
                                Container(
                                  width: 44,
                                  height: 44,
                                  decoration: BoxDecoration(
                                    color: CSAppColors.primary.withValues(alpha: 0.14),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: const Icon(
                                    Icons.meeting_room_outlined,
                                    color: CSAppColors.primary,
                                    size: 22,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        roomName,
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w700,
                                          color: CSAppColors.textPrimary,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Tổng số ghế: $seats ghế',
                                        style: TextStyle(
                                          color: CSAppColors.muted,
                                          fontSize: 12.5,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: (isCalibrated ? CSAppColors.success : CSAppColors.warning)
                                            .withValues(alpha: 0.14),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        '● $status',
                                        style: TextStyle(
                                          color: isCalibrated ? CSAppColors.success : CSAppColors.warning,
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Icon(
                                      Icons.chevron_right,
                                      color: CSAppColors.muted,
                                      size: 20,
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
