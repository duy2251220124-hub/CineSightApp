import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
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

  static const List<Map<String, dynamic>> _fallbackRooms = [
    {'room_id': 'room1', 'name': 'Phòng chiếu 1', 'total_seats': 136, 'is_calibrated': true},
    {'room_id': 'room2', 'name': 'Phòng chiếu 2', 'total_seats': 136, 'is_calibrated': true},
    {'room_id': 'room3', 'name': 'Phòng chiếu 3', 'total_seats': 136, 'is_calibrated': true},
    {'room_id': 'room4', 'name': 'Phòng chiếu 4', 'total_seats': 136, 'is_calibrated': true},
  ];

  Future<void> _loadRooms() async {
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
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chọn phòng chiếu',
              subtitle: '4 phòng chiếu (136 ghế / phòng · 12 hàng A–L)',
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
                  final rawRoomId = (room['room_id'] ?? 'room1').toString().replaceAll('seats_config_', '');
                  final roomName = room['name']?.toString() ??
                      (rawRoomId.startsWith('room')
                          ? 'Phòng chiếu ${rawRoomId.replaceAll('room', '')}'
                          : rawRoomId);
                  final seats = room['total_seats'] ?? 136;
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
                                  '$roomName ($rawRoomId)',
                                  style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                Text(
                                  'Tổng số ghế: $seats ghế (12 hàng A–L: A=8, B–J=11, K=13, L=15)',
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
