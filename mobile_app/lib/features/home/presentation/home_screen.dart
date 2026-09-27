import 'package:flutter/material.dart';

import '../../../theme/app_theme.dart';
import '../../scanner/presentation/scanner_screen.dart';
import '../../../screens/cs_home_screen.dart';
import '../../../screens/cs_warning_screen.dart';
import '../../../screens/cs_warning_detail_screen.dart';
import '../../../widgets/cs_bottom_nav.dart';
import '../../../screens/cs_showtimes_screen.dart';
import '../../../screens/cs_rooms_screen.dart';
import '../../../screens/cs_handover_screen.dart';
import '../../../screens/cs_notification_screen.dart';
import '../../../screens/cs_settings_screen.dart';
import '../../../screens/cs_seat_map_screen.dart';
import '../../../screens/cs_damaged_seat_screen.dart';
import '../../../screens/cs_add_incident_screen.dart';
import '../../../screens/cs_incident_detail_screen.dart';
import '../../../screens/cs_offline_screen.dart';
import '../../../screens/cs_login_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: IndexedStack(
        index: _currentIndex,
        children: [
          // TAB 1: Trang chủ
          CSHomeScreen(
            onShowtimes: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (ctx) => CSShowtimesScreen(
                    onMovieSelected: (_) => Navigator.pop(ctx),
                  ),
                ),
              );
            },
            onRooms: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (ctx) => CSRoomsScreen(
                    onConfirmed: (room) {
                      // MỞ SƠ ĐỒ GHẾ NGỒI (Nhóm C)
                      Navigator.push(
                        ctx,
                        MaterialPageRoute(
                          builder: (ctx2) => CSSeatMapScreen(
                            onReportDamagedSeat: () {
                              // MỞ BÁO CÁO GHẾ HỎNG (Nhóm C)
                              Navigator.push(
                                ctx2,
                                MaterialPageRoute(
                                  builder: (ctx3) => CSDamagedSeatScreen(
                                    onAddPhoto: () {
                                      // MỞ TẠO SỰ CỐ MỚI (Nhóm C)
                                      Navigator.push(
                                        ctx3,
                                        MaterialPageRoute(
                                          builder: (_) =>
                                              const CSAddIncidentScreen(),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      );
                    },
                  ),
                ),
              );
            },
            onHandover: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CSHandoverScreen()),
              );
            },
            onNotifications: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CSNotificationScreen()),
              );
            },
          ),

          // TAB 2: Quét vé
          const ScannerScreen(),

          // TAB 3: Cảnh báo
          CSWarningScreen(
            onWarningSelected: (warning) {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (ctx) => CSWarningDetailScreen(
                    onResolved: () => Navigator.pop(ctx),
                  ),
                ),
              );
            },
            onIgnoreAll: () {
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(const SnackBar(content: Text('Đã bỏ qua tất cả')));
            },
          ),

          // TAB 4: Cài đặt (Đã thay bằng Giao diện thật từ Figma - Nhóm C)
          CSSettingsScreen(
            onNotifications: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CSNotificationScreen()),
              );
            },
            onChangePassword: () {
              // TEST ROUTE: Mở giao diện Offline (Nhóm C)
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (ctx) =>
                      CSOfflineScreen(onRetry: () => Navigator.pop(ctx)),
                ),
              );
            },
            onLogout: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const CSLoginScreen()),
              );
            },
          ),
        ],
      ),
      bottomNavigationBar: CSBottomNav(
        selectedIndex: _currentIndex,
        onChanged: (i) => setState(() => _currentIndex = i),
      ),
    );
  }
}
