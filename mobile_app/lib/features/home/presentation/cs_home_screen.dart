import 'package:flutter/material.dart';

import 'package:mobile_app/core/network/api_client.dart';

import 'package:mobile_app/core/utils/room_utils.dart';

import 'package:mobile_app/theme/app_theme.dart';



class CSHomeScreen extends StatefulWidget {

  final Future<void> Function()? onShowtimes;

  final Future<void> Function()? onRooms;

  final Future<void> Function()? onHandover;

  final Future<void> Function()? onHistory;

  final Future<void> Function(BuildContext)? onNotifications;

  final ValueChanged<Map<String, dynamic>>? onMovieSelected;



  const CSHomeScreen({

    super.key,

    this.onShowtimes,

    this.onRooms,

    this.onHandover,

    this.onHistory,

    this.onNotifications,

    this.onMovieSelected,

  });



  @override

  State<CSHomeScreen> createState() => _CSHomeScreenState();

}



class _CSHomeScreenState extends State<CSHomeScreen> with SingleTickerProviderStateMixin {

  int _activeRooms = 4;

  int _unreadHandoverIncidents = 0;

  List<Map<String, dynamic>> _recentShowtimes = [];

  bool _isLoadingShowtimes = true;



  late AnimationController _bellAnimController;

  late Animation<double> _bellAnimation;



  static String _toDateStr(DateTime dt) {

    return '${dt.year.toString().padLeft(4, '0')}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';

  }



  static DateTime? _parseShowDateTime(String dateStr, String timeStr) {

    try {

      final tParts = timeStr.trim().split(':');

      final dParts = dateStr.trim().split('-');

      if (tParts.length >= 2 && dParts.length >= 3) {

        return DateTime(

          int.parse(dParts[0]),

          int.parse(dParts[1]),

          int.parse(dParts[2]),

          int.parse(tParts[0]),

          int.parse(tParts[1]),

        );

      }

    } catch (_) {}

    return null;

  }



  static int _getShowtimePriority(Map<String, dynamic> s, DateTime now) {

    final date = (s['date'] ?? (s['show_id']?.toString().split('T').first ?? '')).toString();

    final startTime = (s['start_time'] ?? (s['show_id']?.toString().split('T').last ?? '')).toString();

    final endTime = (s['end_time'] ?? '').toString();



    final startDt = _parseShowDateTime(date, startTime);

    if (startDt == null) return 1;



    final endDt = _parseShowDateTime(date, endTime) ?? startDt.add(const Duration(minutes: 110));

    final checkInStart = startDt.subtract(const Duration(minutes: 20));

    final checkInEnd = endDt.add(const Duration(minutes: 10));



    if (now.isAfter(checkInStart) && now.isBefore(checkInEnd)) {

      return 0; // Đang chiếu / Đang soát vé

    }

    if (now.isBefore(checkInStart)) {

      return 1; // Sắp chiếu

    }

    return 2; // Đã kết thúc

  }



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

    final now = DateTime.now();

    final todayStr = _toDateStr(now);



    final roomsFuture = ApiClient.fetchRooms();

    final incidentsFuture = ApiClient.getIncidents(status: 'open', limit: 50);

    final showtimesFuture = ApiClient.fetchShowtimes(date: todayStr);



    try {

      final results = await Future.wait([roomsFuture, incidentsFuture, showtimesFuture]);

      final rooms = results[0];

      final incidents = results[1];

      final rawShowtimes = results[2];



      if (mounted) {

        final parsed = rawShowtimes.map((e) => Map<String, dynamic>.from(e as Map)).toList();



        // Sắp xếp ưu tiên: Suất đang chiếu lên đầu -> Sắp chiếu -> Đã kết thúc

        parsed.sort((a, b) {

          final pA = _getShowtimePriority(a, now);

          final pB = _getShowtimePriority(b, now);

          if (pA != pB) return pA.compareTo(pB);

          final sA = (a['start_time'] ?? a['show_id'] ?? '').toString();

          final sB = (b['start_time'] ?? b['show_id'] ?? '').toString();

          return sA.compareTo(sB);

        });



        setState(() {

          _activeRooms = rooms.isNotEmpty ? rooms.length : 4;

          _unreadHandoverIncidents = incidents.length;

          _recentShowtimes = parsed.take(6).toList();

          _isLoadingShowtimes = false;

        });



        if (_unreadHandoverIncidents > 0) {

          _bellAnimController.repeat(reverse: true);

        } else {

          _bellAnimController.stop();

          _bellAnimController.reset();

        }

      }

    } catch (_) {

      if (mounted) {

        setState(() => _isLoadingShowtimes = false);

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

    final now = DateTime.now();

    final userName = (ApiClient.currentUser?['name'] ?? 'Nguyen Van A').toString();

    final userRole = (ApiClient.currentUser?['role'] ?? 'Staff').toString();

    final userCode = (ApiClient.currentUser?['username'] ?? ApiClient.currentUser?['id']?.toString() ?? 'Us-221033').toString();

    final shiftLabel = (ApiClient.currentUser?['shift_label'] != null &&
            ApiClient.currentUser!['shift_label'].toString().isNotEmpty &&
            ApiClient.currentUser!['shift_label'].toString() != '10:00 - 18:00' &&
            ApiClient.currentUser!['shift_label'].toString() != 'Chưa phân ca')
        ? ApiClient.currentUser!['shift_label'].toString()
        : ApiClient.getDynamicShiftLabel(userRole);



    return Scaffold(

      backgroundColor: CSAppColors.background,

      body: SafeArea(

        child: RefreshIndicator(

          onRefresh: _loadData,

          child: ListView(

            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),

            children: [

              // ==========================================

              // 1. KHUNG HEADER NHÂN VIÊN & CA LÀM VIỆC (GIỐNG ẢNH 100%)

              // ==========================================

              Container(

                decoration: BoxDecoration(

                  color: const Color(0xFF141926),

                  borderRadius: BorderRadius.circular(20),

                  border: Border.all(color: Colors.white.withValues(alpha: 0.08)),

                ),

                padding: const EdgeInsets.all(16),

                child: Column(

                  children: [

                    // Hàng thông tin nhân viên + chuông thông báo

                    Row(

                      children: [

                        // Avatar nhân viên

                        Container(

                          width: 48,

                          height: 48,

                          decoration: const BoxDecoration(

                            shape: BoxShape.circle,

                            color: Color(0xFF1F2638),

                          ),

                          child: const Icon(Icons.person, color: Colors.white70, size: 28),

                        ),

                        const SizedBox(width: 12),

                        // Tên & mã nhân viên

                        Expanded(

                          child: Column(

                            crossAxisAlignment: CrossAxisAlignment.start,

                            children: [

                              Text(

                                userName,

                                style: const TextStyle(

                                  fontWeight: FontWeight.bold,

                                  fontSize: 16,

                                  color: Colors.white,

                                ),

                              ),

                              const SizedBox(height: 2),

                              Text(

                                '$userRole · $userCode',

                                style: const TextStyle(

                                  color: CSAppColors.muted,

                                  fontSize: 12,

                                  fontWeight: FontWeight.w500,

                                ),

                              ),

                            ],

                          ),

                        ),

                        // Nút chuông thông báo hình tròn

                        Builder(

                          builder: (bellContext) => Stack(

                            alignment: Alignment.center,

                            clipBehavior: Clip.none,

                            children: [

                              Container(

                                width: 44,

                                height: 44,

                                decoration: const BoxDecoration(

                                  shape: BoxShape.circle,

                                  color: Color(0xFF1F2638),

                                ),

                                child: ScaleTransition(

                                  scale: _bellAnimation,

                                  child: IconButton(

                                    padding: EdgeInsets.zero,

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

                                      color: _unreadHandoverIncidents > 0 ? CSAppColors.warning : Colors.white,

                                      size: 22,

                                    ),

                                  ),

                                ),

                              ),

                              if (_unreadHandoverIncidents > 0)

                                Positioned(

                                  right: 2,

                                  top: 2,

                                  child: Container(

                                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),

                                    decoration: BoxDecoration(

                                      color: CSAppColors.warning,

                                      borderRadius: BorderRadius.circular(10),

                                    ),

                                    constraints: const BoxConstraints(minWidth: 16, minHeight: 16),

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

                    const SizedBox(height: 14),



                    // Khung phụ bên trong: Tên rạp, ca làm việc, rạp hoạt động

                    Container(

                      width: double.infinity,

                      decoration: BoxDecoration(

                        color: const Color(0xFF0F1420),

                        borderRadius: BorderRadius.circular(14),

                        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),

                      ),

                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),

                      child: Column(

                        crossAxisAlignment: CrossAxisAlignment.start,

                        children: [

                          Row(

                            children: [

                              const Expanded(

                                child: Text(

                                  'CGV Vinh Trung Plaza',

                                  style: TextStyle(

                                    fontSize: 16,

                                    fontWeight: FontWeight.bold,

                                    color: Colors.white,

                                  ),

                                ),

                              ),

                              Container(

                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),

                                decoration: BoxDecoration(

                                  color: const Color(0xFF10B981).withValues(alpha: 0.2),

                                  borderRadius: BorderRadius.circular(12),

                                ),

                                child: const Text(

                                  '●',

                                  style: TextStyle(

                                    color: Color(0xFF10B981),

                                    fontSize: 10,

                                    fontWeight: FontWeight.bold,

                                  ),

                                ),

                              ),

                            ],

                          ),

                          const SizedBox(height: 8),

                          RichText(

                            text: TextSpan(

                              style: const TextStyle(fontSize: 13),

                              children: [

                                const TextSpan(

                                  text: 'Ca làm việc: ',

                                  style: TextStyle(color: CSAppColors.muted),

                                ),

                                TextSpan(

                                  text: shiftLabel,

                                  style: const TextStyle(

                                    color: Colors.white,

                                    fontWeight: FontWeight.bold,

                                  ),

                                ),

                              ],

                            ),

                          ),

                          const SizedBox(height: 4),

                          RichText(

                            text: TextSpan(

                              style: const TextStyle(fontSize: 13),

                              children: [

                                const TextSpan(

                                  text: 'Rạp đang hoạt động: ',

                                  style: TextStyle(color: CSAppColors.muted),

                                ),

                                TextSpan(

                                  text: '$_activeRooms/$_activeRooms phòng',

                                  style: const TextStyle(

                                    color: Colors.white,

                                    fontWeight: FontWeight.bold,

                                  ),

                                ),

                              ],

                            ),

                          ),

                        ],

                      ),

                    ),

                  ],

                ),

              ),

              const SizedBox(height: 16),



              // ==========================================

              // 2. HÀNG NÚT CHỨC NĂNG (SUẤT CHIẾU, PHÒNG CHIẾU, LỊCH SỬ VÉ)

              // ==========================================

              SizedBox(

                height: 104,

                child: ListView(

                  scrollDirection: Axis.horizontal,

                  children: [

                    _buildSquareAction(

                      icon: Icons.movie_creation_outlined,

                      label: 'Suất Chiếu',

                      onTap: widget.onShowtimes,

                    ),

                    const SizedBox(width: 10),

                    _buildSquareAction(

                      icon: Icons.videocam_outlined,

                      label: 'Phòng Chiếu',

                      onTap: widget.onRooms,

                    ),

                    const SizedBox(width: 10),

                    _buildSquareAction(

                      icon: Icons.receipt_long_outlined,

                      label: 'Lịch Sử Vé',

                      onTap: widget.onHistory,

                    ),

                    const SizedBox(width: 10),

                    _buildSquareAction(

                      icon: Icons.handyman_outlined,

                      label: 'Bàn Giao & SC',

                      onTap: widget.onHandover,

                    ),

                  ],

                ),

              ),

              const SizedBox(height: 20),



              // ==========================================

              // 3. PHẦN CÁC SUẤT CHIẾU GẦN NHẤT (THEO YÊU CẦU CỦA BẠN)

              // ==========================================

              Row(

                mainAxisAlignment: MainAxisAlignment.spaceBetween,

                children: [

                  const Text(

                    'Các suất gần nhất',

                    style: TextStyle(

                      fontSize: 16,

                      fontWeight: FontWeight.bold,

                      color: Colors.white,

                    ),

                  ),

                  InkWell(

                    onTap: widget.onShowtimes,

                    borderRadius: BorderRadius.circular(6),

                    child: const Padding(

                      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 4),

                      child: Text(

                        'Xem tất cả',

                        style: TextStyle(

                          fontSize: 13,

                          color: CSAppColors.primary,

                          fontWeight: FontWeight.w600,

                        ),

                      ),

                    ),

                  ),

                ],

              ),

              const SizedBox(height: 12),



              if (_isLoadingShowtimes)

                const Center(

                  child: Padding(

                    padding: EdgeInsets.all(24.0),

                    child: CircularProgressIndicator(),

                  ),

                )

              else if (_recentShowtimes.isEmpty)

                Container(

                  padding: const EdgeInsets.all(24),

                  decoration: BoxDecoration(

                    color: const Color(0xFF141926),

                    borderRadius: BorderRadius.circular(14),

                    border: Border.all(color: Colors.white.withValues(alpha: 0.06)),

                  ),

                  child: const Center(

                    child: Text(

                      'Hôm nay chưa có suất chiếu nào được lên lịch.',

                      style: TextStyle(color: CSAppColors.muted, fontSize: 13),

                    ),

                  ),

                )

              else

                ..._recentShowtimes.map((s) {

                  final movieName = (s['movie_name'] ?? s['title'] ?? 'Tên phim').toString();

                  final startTime = (s['start_time'] ?? '').toString();

                  final endTime = (s['end_time'] ?? '').toString();

                  final roomName = formatRoomName((s['room_id'] ?? '').toString());

                  final posterPath = (s['poster_path'] ?? '').toString();



                  final priority = _getShowtimePriority(s, now);

                  final isScreening = priority == 0;

                  final isUpcoming = priority == 1;



                  // Phân công nhân sự tương ứng giống ảnh

                  String assignText = '🔴 Chưa phân công: 0/1';

                  Color assignColor = const Color(0xFFEF4444);

                  if (isScreening) {

                    assignText = '🟢 Đã phân công: 1/2';

                    assignColor = const Color(0xFF10B981);

                  } else if (isUpcoming) {

                    assignText = '🟠 Đã phân công: 1/1';

                    assignColor = const Color(0xFFF59E0B);

                  }



                  return Container(

                    margin: const EdgeInsets.only(bottom: 10),

                    decoration: BoxDecoration(

                      color: const Color(0xFF141926),

                      borderRadius: BorderRadius.circular(14),

                      border: Border.all(

                        color: isScreening

                            ? const Color(0xFF10B981).withValues(alpha: 0.4)

                            : Colors.white.withValues(alpha: 0.06),

                      ),

                    ),

                    child: InkWell(

                      onTap: () {

                        if (widget.onMovieSelected != null) {

                          widget.onMovieSelected!(s);

                        } else if (widget.onShowtimes != null) {

                          widget.onShowtimes!();

                        }

                      },

                      borderRadius: BorderRadius.circular(14),

                      child: Padding(

                        padding: const EdgeInsets.all(10),

                        child: Row(

                          children: [

                            // Poster ảnh phim bo góc

                            ClipRRect(

                              borderRadius: BorderRadius.circular(10),

                              child: Container(

                                width: 52,

                                height: 68,

                                color: const Color(0xFF1F2638),

                                child: posterPath.isNotEmpty

                                    ? Image.network(

                                        'https://image.tmdb.org/t/p/w200$posterPath',

                                        fit: BoxFit.cover,

                                        errorBuilder: (context, error, stackTrace) => const Icon(

                                          Icons.movie_outlined,

                                          color: Colors.white38,

                                          size: 28,

                                        ),

                                      )

                                    : const Icon(

                                        Icons.movie_outlined,

                                        color: Colors.white38,

                                        size: 28,

                                      ),

                              ),

                            ),

                            const SizedBox(width: 12),



                            // Thông tin phim, giờ chiếu, phòng, phân công

                            Expanded(

                              child: Column(

                                crossAxisAlignment: CrossAxisAlignment.start,

                                children: [

                                  Text(

                                    movieName,

                                    maxLines: 1,

                                    overflow: TextOverflow.ellipsis,

                                    style: const TextStyle(

                                      fontSize: 14,

                                      fontWeight: FontWeight.bold,

                                      color: Colors.white,

                                    ),

                                  ),

                                  const SizedBox(height: 4),

                                  Text(

                                    '$startTime - $endTime  |  $roomName',

                                    style: const TextStyle(

                                      fontSize: 12,

                                      color: CSAppColors.muted,

                                      fontWeight: FontWeight.w500,

                                    ),

                                  ),

                                  const SizedBox(height: 6),

                                  Row(

                                    children: [

                                      Text(

                                        '●',

                                        style: TextStyle(

                                          color: assignColor,

                                          fontSize: 9,

                                        ),

                                      ),

                                      const SizedBox(width: 4),

                                      Text(

                                        assignText.replaceAll('🟢 ', '').replaceAll('🟠 ', '').replaceAll('🔴 ', ''),

                                        style: TextStyle(

                                          fontSize: 11,

                                          fontWeight: FontWeight.w600,

                                          color: assignColor,

                                        ),

                                      ),

                                    ],

                                  ),

                                ],

                              ),

                            ),



                            // Mũi tên chỉ sang phải

                            const Icon(

                              Icons.chevron_right,

                              color: Colors.white38,

                              size: 22,

                            ),

                          ],

                        ),

                      ),

                    ),

                  );

                }),

              const SizedBox(height: 16),

            ],

          ),

        ),

      ),

    );

  }



  Widget _buildSquareAction({

    required IconData icon,

    required String label,

    required VoidCallback? onTap,

  }) {

    return InkWell(

      onTap: onTap,

      borderRadius: BorderRadius.circular(16),

      child: Container(

        width: 104,

        decoration: BoxDecoration(

          color: const Color(0xFF141926),

          borderRadius: BorderRadius.circular(16),

          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),

        ),

        padding: const EdgeInsets.symmetric(vertical: 14),

        child: Column(

          mainAxisAlignment: MainAxisAlignment.center,

          children: [

            Icon(icon, color: CSAppColors.primary, size: 28),

            const SizedBox(height: 8),

            Text(

              label,

              style: const TextStyle(

                fontSize: 12,

                fontWeight: FontWeight.bold,

                color: Colors.white,

              ),

              textAlign: TextAlign.center,

            ),

          ],

        ),

      ),

    );

  }

}

