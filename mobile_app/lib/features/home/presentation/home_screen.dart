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

import '../../../screens/cs_offline_screen.dart';
import '../../../screens/cs_login_screen.dart';
import '../../../mock/mock_data.dart';
import '../../../core/utils/show_id_utils.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;

  CSMockMovie _selectedMovie = CSMockData.movies.first;

  String get _currentShowId =>
      toShowId(_selectedMovie.date, _selectedMovie.time);

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

  /// Bấm tab khác -> chuyển tab. Bấm lại tab đang mở -> quay về màn gốc của tab.
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
                          setState(() => _selectedMovie = movie);
                          Navigator.pop(ctx);
                        },
                      ),
                    ));
                  },
                  onRooms: () {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSRoomsScreen(
                        onConfirmed: (room) {
                          Navigator.push(ctx, MaterialPageRoute(
                            builder: (ctx2) => CSSeatMapScreen(
                              onReportDamagedSeat: () {
                                Navigator.push(ctx2, MaterialPageRoute(
                                  builder: (ctx3) => CSDamagedSeatScreen(
                                    onAddPhoto: (seats) {
                                      Navigator.push(ctx3, MaterialPageRoute(
                                        builder: (ctx4) => CSAddIncidentScreen(
                                          reportedSeats: seats,
                                          // Tạo xong: quay về Sơ đồ ghế để thấy ghế vừa báo hư (màu cam).
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
                builder: (navCtx) => ScannerScreen(roomId: _selectedMovie.roomId, showId: _currentShowId)
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
