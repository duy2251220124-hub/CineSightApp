import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/utils/show_id_utils.dart';

import 'package:mobile_app/theme/app_theme.dart';
import '../../scanner/presentation/scanner_screen.dart';
import 'package:mobile_app/features/scanner/presentation/cs_scan_history_screen.dart';
import 'package:mobile_app/features/home/presentation/cs_home_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_warning_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_warning_detail_screen.dart';
import 'package:mobile_app/core/widgets/cs_bottom_nav.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/features/rooms/presentation/cs_showtimes_screen.dart';
import 'package:mobile_app/features/rooms/presentation/cs_rooms_screen.dart';
import 'package:mobile_app/features/rooms/presentation/cs_seat_map_screen.dart';
import 'package:mobile_app/features/alerts/presentation/cs_handover_screen.dart';
import 'package:mobile_app/features/notifications/presentation/cs_notification_screen.dart';
import 'package:mobile_app/features/settings/presentation/cs_settings_screen.dart';
import 'package:mobile_app/core/network/presentation/cs_offline_screen.dart';
import 'package:mobile_app/features/auth/presentation/cs_login_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;
  int _aiAlertCount = 0; // Đếm số lượng cảnh báo từ AI Service
  int _lastKnownAiAlertCount = 0;
  Timer? _aiAlertPollTimer;

  final GlobalKey<CSWarningScreenState> _warningKey = GlobalKey<CSWarningScreenState>();

  late final Map<String, dynamic> _selectedShowtime = {
    'roomId': CSActiveShowtime.roomId,
    'showId': CSActiveShowtime.showId,
  };

  final List<GlobalKey<NavigatorState>> _navigatorKeys = [
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
  ];

  @override
  void initState() {
    super.initState();
    // Bắt đầu timer kiểm tra cảnh báo AI định kỳ mỗi 3 giây
    _pollAiAlerts();
    _aiAlertPollTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      _pollAiAlerts();
    });
  }

  @override
  void dispose() {
    _aiAlertPollTimer?.cancel();
    super.dispose();
  }

  /// Kiểm tra ngầm cảnh báo từ hệ thống AI (chỉ lấy alerts, không trộn lẫn với incidents)
  Future<void> _pollAiAlerts() async {
    try {
      final alerts = await ApiClient.fetchAlerts();
      final activeAlerts = alerts.where((a) => (a['resolved'] == 0 || a['resolved'] == false)).toList();
      final currentCount = activeAlerts.length;

      if (!mounted) return;

      if (currentCount > _lastKnownAiAlertCount && _lastKnownAiAlertCount >= 0) {
        // Có cảnh báo AI mới sinh ra từ server!
        HapticFeedback.heavyImpact();

        // Trích xuất 3 thông số nghiệp vụ từ cảnh báo AI mới nhất (chống spam thông báo)
        final latestAlert = activeAlerts.isNotEmpty ? activeAlerts.first : null;
        final roomName = latestAlert != null
            ? formatRoomName(latestAlert['room_id']?.toString())
            : 'Phòng chiếu';
        final showId = latestAlert?['show_id']?.toString() ?? '';
        final showTime = showId.contains('T') ? showId.split('T')[1] : showId;
        final scannedTickets = latestAlert?['scanned_tickets_count'] ?? 0;
        final detectedPeople = latestAlert?['detected_people_count'] ?? 0;
        final rawSeats = (latestAlert?['all_alerted_seats'] as List?)?.map((s) => s.toString()).toList() ?? [];
        final seatsDisplay = rawSeats.isNotEmpty
            ? rawSeats.join(', ')
            : (latestAlert?['seat_id'] ?? latestAlert?['seats'] ?? 'N/A').toString();
        final alertSeatsCount = latestAlert?['room_alert_count'] ?? currentCount;

        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: const Color(0xFFDC2626), // Đỏ cảnh báo nổi bật
            duration: const Duration(seconds: 8),
            behavior: SnackBarBehavior.floating,
            margin: const EdgeInsets.fromLTRB(12, 0, 12, 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            content: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 30),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '🚨 CẢNH BÁO AI: $roomName • Suất $showTime',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        '🎟️ Vé đã quét: $scannedTickets  |  👥 Người trong rạp: $detectedPeople',
                        style: const TextStyle(fontSize: 11, color: Colors.white),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '⚠️ $alertSeatsCount ghế cảnh báo: $seatsDisplay',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.amberAccent),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            action: SnackBarAction(
              label: 'XEM NGAY',
              textColor: Colors.amberAccent,
              onPressed: () {
                _onTabTapped(2); // Chuyển sang Tab Cảnh báo
              },
            ),
          ),
        );

        // Làm mới màn hình cảnh báo nếu đang mở
        _warningKey.currentState?.loadAlerts();
      }

      setState(() {
        _aiAlertCount = currentCount;
        _lastKnownAiAlertCount = currentCount;
      });
    } catch (_) {
      // Bỏ qua lỗi kết nối tạm thời
    }
  }

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
      if (index == 2) {
        _warningKey.currentState?.loadAlerts();
      }
      return;
    }
    setState(() => _currentIndex = index);
    if (index == 2) {
      _warningKey.currentState?.loadAlerts();
    }
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
            // TAB 0: TRANG CHỦ
            Navigator(
              key: _navigatorKeys[0],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSHomeScreen(
                  onShowtimes: () async {
                    await Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSShowtimesScreen(
                        onMovieSelected: (movie) {
                          final showId = (movie['show_id'] ?? movie['id'] ?? _selectedShowtime['showId']).toString();
                          final roomId = movie['room_id'] != null
                              ? movie['room_id'].toString().replaceAll('seats_config_', '')
                              : _selectedShowtime['roomId'];
                          final movieTitle = movie['movie_name']?.toString() ?? movie['title']?.toString() ?? '';

                          setState(() {
                            _selectedShowtime['showId'] = showId;
                            _selectedShowtime['roomId'] = roomId;
                          });
                          CSActiveShowtime.update(
                            roomId: roomId,
                            showId: showId,
                            movieTitle: movieTitle,
                          );
                          Navigator.push(
                            ctx,
                            MaterialPageRoute(
                              builder: (_) => CSSeatMapScreen(
                                roomId: roomId,
                                showId: showId,
                                onGoToScanner: (targetRoom, targetShow, targetTitle) {
                                  setState(() {
                                    _selectedShowtime['roomId'] = targetRoom;
                                    _selectedShowtime['showId'] = targetShow;
                                  });
                                  CSActiveShowtime.update(
                                    roomId: targetRoom,
                                    showId: targetShow,
                                    movieTitle: targetTitle,
                                  );
                                  Navigator.of(navCtx).popUntil((route) => route.isFirst);
                                  _onTabTapped(1);
                                },
                              ),
                            ),
                          );
                        },
                      ),
                    ));
                  },
                  onRooms: () async {
                    // Chọn phòng chiếu -> Mở vào màn hình Sơ đồ ghế (CSSeatMapScreen) của phòng đó
                    await Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSRoomsScreen(
                        onConfirmed: (room) {
                          final rId = (room['room_id'] ?? 'room1').toString().replaceAll('seats_config_', '');
                          final currentShowForRoom = (_selectedShowtime['roomId'] == rId &&
                                  _selectedShowtime['showId'] != null &&
                                  _selectedShowtime['showId'] != 'auto')
                              ? _selectedShowtime['showId'].toString()
                              : '';

                          setState(() {
                            _selectedShowtime['roomId'] = rId;
                          });

                          Navigator.push(
                            ctx,
                            MaterialPageRoute(
                              builder: (seatMapCtx) => CSSeatMapScreen(
                                roomId: rId,
                                showId: currentShowForRoom,
                                onGoToScanner: (targetRoom, targetShow, targetTitle) {
                                  setState(() {
                                    _selectedShowtime['roomId'] = targetRoom;
                                    _selectedShowtime['showId'] = targetShow;
                                  });
                                  CSActiveShowtime.update(
                                    roomId: targetRoom,
                                    showId: targetShow,
                                    movieTitle: targetTitle,
                                  );
                                  Navigator.of(navCtx).popUntil((route) => route.isFirst);
                                  _onTabTapped(1);
                                },
                              ),
                            ),
                          );
                        },
                      ),
                    ));
                  },
                  onHandover: () async {
                    await Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSHandoverScreen()));
                  },
                  onHistory: () async {
                    await Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSScanHistoryScreen()));
                  },
                  onMovieSelected: (movie) {
                    final showId = (movie['show_id'] ?? movie['id'] ?? _selectedShowtime['showId']).toString();
                    final roomId = movie['room_id'] != null
                        ? movie['room_id'].toString().replaceAll('seats_config_', '')
                        : _selectedShowtime['roomId'];
                    final movieTitle = movie['movie_name']?.toString() ?? movie['title']?.toString() ?? '';

                    setState(() {
                      _selectedShowtime['showId'] = showId;
                      _selectedShowtime['roomId'] = roomId;
                    });
                    CSActiveShowtime.update(
                      roomId: roomId,
                      showId: showId,
                      movieTitle: movieTitle,
                    );
                    Navigator.push(
                      navCtx,
                      MaterialPageRoute(
                        builder: (_) => CSSeatMapScreen(
                          roomId: roomId,
                          showId: showId,
                          onGoToScanner: (targetRoom, targetShow, targetTitle) {
                            setState(() {
                              _selectedShowtime['roomId'] = targetRoom;
                              _selectedShowtime['showId'] = targetShow;
                            });
                            CSActiveShowtime.update(
                              roomId: targetRoom,
                              showId: targetShow,
                              movieTitle: targetTitle,
                            );
                            Navigator.of(navCtx).popUntil((route) => route.isFirst);
                            _onTabTapped(1);
                          },
                        ),
                      ),
                    );
                  },
                  onNotifications: (bellCtx) async {
                    // Icon chuông nhỏ góc trên bên phải: Thông báo bàn giao ca & sự cố rạp
                    await showCSNotificationPopover(
                      navCtx,
                      anchorContext: bellCtx,
                      onViewAll: () async {
                        await Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSNotificationScreen()));
                      },
                    );
                  },
                )
              )
            ),
            
            // TAB 1: QUÉT VÉ (SCANNER)
            Navigator(
              key: _navigatorKeys[1],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => ScannerScreen(
                  roomId: _selectedShowtime['roomId'],
                  showId: _selectedShowtime['showId'],
                  onShowtimeChanged: (rId, sId) {
                    setState(() {
                      _selectedShowtime['roomId'] = rId;
                      _selectedShowtime['showId'] = sId;
                    });
                  },
                )
              )
            ),

            // TAB 2: CẢNH BÁO TỪ AI SERVICE (Icon chuông ở thanh điều hướng dưới)
            Navigator(
              key: _navigatorKeys[2],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSWarningScreen(
                  key: _warningKey,
                  onWarningSelected: (warning) {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSWarningDetailScreen(
                        alertId: warning['id'] ?? 1,
                        alertData: warning,
                        onResolved: () {
                          _warningKey.currentState?.loadAlerts();
                          _pollAiAlerts();
                        },
                      ),
                    ));
                  },
                  onIgnoreAll: () {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã bỏ qua tất cả')));
                  },
                )
              )
            ),

            // TAB 3: CÀI ĐẶT
            Navigator(
              key: _navigatorKeys[3],
              onGenerateRoute: (settings) => MaterialPageRoute(
                builder: (navCtx) => CSSettingsScreen(
                  onNotifications: () {
                    Navigator.push(navCtx, MaterialPageRoute(builder: (_) => const CSNotificationScreen()));
                  },
                  onSyncOffline: () {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSOfflineScreen(onRetry: () => Navigator.pop(ctx)),
                    ));
                  },
                  onChangePassword: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Vui lòng liên hệ Quản lý rạp trên Web Admin để cấp lại mật khẩu.'),
                      ),
                    );
                  },
                  onLogout: () {
                    ApiClient.logout();
                    Navigator.pushAndRemoveUntil(
                      context, 
                      MaterialPageRoute(builder: (_) => Builder(
                        builder: (ctx) => CSLoginScreen(
                          onLogin: () {
                            Navigator.pushReplacement(
                              ctx,
                              MaterialPageRoute(builder: (_) => const HomeShell()),
                            );
                          },
                        ),
                      )),
                      (route) => false,
                    );
                  },
                )
              )
            ),
          ],
        ),
        bottomNavigationBar: CSBottomNav(
          selectedIndex: _currentIndex,
          onChanged: _onTabTapped,
          alertCount: _aiAlertCount, // Badge đỏ hiển thị đúng số cảnh báo AI
        ),
      ),
    );
  }
}
