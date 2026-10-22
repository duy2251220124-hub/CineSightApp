import os

content = """import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../scanner/presentation/scanner_screen.dart';
import 'package:mobile_app/features/home/presentation/cs_home_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_warning_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_warning_detail_screen.dart';
import 'package:mobile_app/core/widgets/cs_bottom_nav.dart';
import 'package:mobile_app/features/rooms/presentation/cs_showtimes_screen.dart';
import 'package:mobile_app/features/rooms/presentation/cs_rooms_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_handover_screen.dart';
import 'package:mobile_app/features/notifications/presentation/cs_notification_screen.dart';
import 'package:mobile_app/features/settings/presentation/cs_settings_screen.dart';
import 'package:mobile_app/features/rooms/presentation/cs_seat_map_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_damaged_seat_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_add_incident_screen.dart';
import 'package:mobile_app/core/network/presentation/cs_offline_screen.dart';
import 'package:mobile_app/features/auth/presentation/cs_login_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;

  Map<String, dynamic> _selectedShowtime = {
    'roomId': 'room1',
    'showId': '2026-09-25T19:30'
  };

  final List<GlobalKey<NavigatorState>> _navigatorKeys = [
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
  ];

  Future<bool> _systemBackButtonPressed() async {
    final navigator = _navigatorKeys[_currentIndex].currentState;
    if (navigator != null && navigator.canPop()) {
      navigator.pop();
      return false; 
    }
    if (_currentIndex != 0) {
      setState(() { _currentIndex = 0; });
      return false;
    }
    return true; 
  }

  void _onTabTapped(int index) {
    if (index == _currentIndex) {
      _navigatorKeys[index].currentState?.popUntil((route) => route.isFirst);
      return;
    }
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) { if (!didPop) _systemBackButtonPressed(); },
      child: Scaffold(
        backgroundColor: CSAppColors.background,
        body: IndexedStack(
          index: _currentIndex,
          children: [
            // TAB 0
            Navigator(
              key: _navigatorKeys[0],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSHomeScreen(
                  onShowtimes: () {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSShowtimesScreen(
                        onMovieSelected: (movie) {
                          setState(() {
                            _selectedShowtime['showId'] = movie['id'] ?? '2026-09-25T19:30';
                          });
                          Navigator.pop(ctx);
                        },
                      ),
                    ));
                  },
                  onRooms: () {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSRoomsScreen(
                        onConfirmed: (room) {
                          setState(() {
                            _selectedShowtime['roomId'] = room['room_id'] ?? 'room1';
                          });
                          Navigator.push(ctx, MaterialPageRoute(
                            builder: (ctx2) => CSSeatMapScreen(
                              onReportDamagedSeat: () {
                                Navigator.push(ctx2, MaterialPageRoute(
                                  builder: (ctx3) => CSDamagedSeatScreen(
                                    onAddPhoto: (seats) {
                                      Navigator.push(ctx3, MaterialPageRoute(
                                        builder: (ctx4) => CSAddIncidentScreen(
                                          reportedSeats: seats,
                                          onSubmit: () => Navigator.of(ctx4)
                                            ..pop()
                                            ..pop(),
                                        ),
                                      ));
                                    },
                                  ),
                                ));
                              },
                            ),
                          ));
                        },
                      ),
                    ));
                  },
                  onHandover: () {
                    Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSHandoverScreen()));
                  },
                  onNotifications: (bellCtx) {
                    showCSNotificationPopover(
                      navCtx,
                      anchorContext: bellCtx,
                      onViewAll: () {
                        Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSNotificationScreen()));
                      },
                    );
                  },
                )
              )
            ),
            
            // TAB 1
            Navigator(
              key: _navigatorKeys[1],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => ScannerScreen(
                  roomId: _selectedShowtime['roomId'],
                  showId: _selectedShowtime['showId']
                )
              )
            ),

            // TAB 2
            Navigator(
              key: _navigatorKeys[2],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSWarningScreen(
                  onWarningSelected: (warning) {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSWarningDetailScreen(
                        onResolved: () => Navigator.pop(ctx),
                      ),
                    ));
                  },
                  onIgnoreAll: () {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã bỏ qua tất cả')));
                  },
                )
              )
            ),

            // TAB 3
            Navigator(
              key: _navigatorKeys[3],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSSettingsScreen(
                  onNotifications: () {
                    Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSNotificationScreen()));
                  },
                  onChangePassword: () {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSOfflineScreen(onRetry: () => Navigator.pop(ctx)),
                    ));
                  },
                  onLogout: () {
                    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const CSLoginScreen()));
                  },
                )
              )
            ),
          ],
        ),
        bottomNavigationBar: CSBottomNav(
          selectedIndex: _currentIndex,
          onChanged: _onTabTapped,
        ),
      ),
    );
  }
}
"""

with open('lib/features/home/presentation/home_screen.dart', 'w', encoding='utf-8') as f:
    f.write(content)
