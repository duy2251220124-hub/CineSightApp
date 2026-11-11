import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_app/core/database/hive_service.dart';
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

class _CSHomeScreenState extends State<CSHomeScreen>
    with SingleTickerProviderStateMixin {
  int _activeRooms = 4;
  int _totalTodayShowtimes = 12;
  int _unreadHandoverIncidents = 0;
  List<Map<String, dynamic>> _recentShowtimes = [];
  bool _isLoadingShowtimes = true;
  Uint8List? _avatarBytes;

  late AnimationController _bellAnimController;
  late Animation<double> _bellAnimation;

  static const Color _brandBlue = Color(0xFF2464F6);
  static const Color _statusGreen = Color(0xFF13843B);
  static const Color _statusGreenDot = Color(0xFF18A34A);
  static const Color _statusGreenBg = Color(0xFFDCFCE8);

  String get _userKey {
    final u = ApiClient.currentUser;
    return (u?['username'] ?? u?['id']?.toString() ?? 'default_staff')
        .toString();
  }

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
    final date =
        (s['date'] ?? (s['show_id']?.toString().split('T').first ?? ''))
            .toString();
    final startTime =
        (s['start_time'] ?? (s['show_id']?.toString().split('T').last ?? ''))
            .toString();
    final endTime = (s['end_time'] ?? '').toString();

    final startDt = _parseShowDateTime(date, startTime);
    if (startDt == null) return 1;

    final endDt =
        _parseShowDateTime(date, endTime) ??
        startDt.add(const Duration(minutes: 110));
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
    _bellAnimation = Tween<double>(begin: 1.0, end: 1.18).animate(
      CurvedAnimation(parent: _bellAnimController, curve: Curves.easeInOut),
    );

    HiveService.avatarRevision.addListener(_onAvatarChanged);
    _loadSavedAvatar();
    _loadData();
  }

  void _onAvatarChanged() {
    if (!mounted) return;
    setState(() {
      _loadSavedAvatar();
    });
  }

  void _loadSavedAvatar() {
    final savedB64 = HiveService.getEmployeeAvatar(_userKey);
    if (savedB64 != null && savedB64.isNotEmpty) {
      try {
        _avatarBytes = base64Decode(savedB64);
      } catch (_) {
        _avatarBytes = null;
      }
    } else {
      _avatarBytes = null;
    }
  }

  Future<void> _loadData() async {
    _loadSavedAvatar();
    final now = DateTime.now();
    final todayStr = _toDateStr(now);

    final roomsFuture = ApiClient.fetchRooms();
    final incidentsFuture = ApiClient.getIncidents(status: 'open', limit: 50);
    final showtimesFuture = ApiClient.fetchShowtimes(date: todayStr);

    try {
      final results = await Future.wait([
        roomsFuture,
        incidentsFuture,
        showtimesFuture,
      ]);
      final rooms = results[0];
      final incidents = results[1];
      final rawShowtimes = results[2];

      if (mounted) {
        final parsed = rawShowtimes
            .map((e) => Map<String, dynamic>.from(e as Map))
            .toList();

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
          _totalTodayShowtimes = parsed.isNotEmpty ? parsed.length : 12;
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
    HiveService.avatarRevision.removeListener(_onAvatarChanged);
    _bellAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool isLight = CSAppColors.isLight;
    final Color bgColor = CSAppColors.background;
    final Color cardColor = CSAppColors.surface;
    final Color textPrimary = CSAppColors.textPrimary;
    final Color textSecondary = CSAppColors.muted;

    final now = DateTime.now();
    final userName =
        (ApiClient.currentUser?['name'] ?? 'Phạm Ngọc Linh').toString();
    final userRole = (ApiClient.currentUser?['role'] ?? 'Soát vé').toString();
    final userIdOrCode =
        (ApiClient.currentUser?['id']?.toString() ??
                ApiClient.currentUser?['username'] ??
                '3')
            .toString();
    final shiftLabel =
        (ApiClient.currentUser?['shift_label'] != null &&
            ApiClient.currentUser!['shift_label'].toString().isNotEmpty &&
            ApiClient.currentUser!['shift_label'].toString() !=
                '10:00 - 18:00' &&
            ApiClient.currentUser!['shift_label'].toString() != 'Chưa phân ca')
        ? ApiClient.currentUser!['shift_label'].toString()
        : ApiClient.getDynamicShiftLabel(userRole);

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: (isLight ? SystemUiOverlayStyle.dark : SystemUiOverlayStyle.light)
          .copyWith(statusBarColor: Colors.transparent),
      child: Scaffold(
        backgroundColor: bgColor,
        body: SafeArea(
          bottom: false,
          child: RefreshIndicator(
            color: _brandBlue,
            backgroundColor: cardColor,
            onRefresh: _loadData,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 110),
              children: [
                // =========================================================
                // 1. THÔNG TIN NHÂN VIÊN (HEADER - Figma 34:2)
                // (Nút thay đổi ảnh đại diện đã chuyển sang màn hình Cài đặt)
                // =========================================================
                Row(
                  children: [
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isLight
                            ? const Color(0xFFE2E8F0)
                            : const Color(0xFF1E293B),
                        border: Border.all(
                          color: isLight
                              ? Colors.white
                              : const Color(0xFF2B3851),
                          width: 2.2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF0F172A).withValues(
                              alpha: isLight ? 0.08 : 0.25,
                            ),
                            blurRadius: 10,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: ClipOval(
                        child: _avatarBytes != null
                            ? Image.memory(
                                _avatarBytes!,
                                width: 50,
                                height: 50,
                                fit: BoxFit.cover,
                              )
                            : Container(
                                color: isLight
                                    ? const Color(0xFFDBEAFE)
                                    : _brandBlue.withValues(alpha: 0.2),
                                child: const Icon(
                                  Icons.person_rounded,
                                  color: _brandBlue,
                                  size: 30,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            userName,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 17.3,
                              color: textPrimary,
                              height: 1.18,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                '$userRole - $userIdOrCode',
                                style: TextStyle(
                                  color: textSecondary,
                                  fontSize: 13.7,
                                  fontWeight: FontWeight.w400,
                                ),
                              ),
                              const SizedBox(width: 2),
                              Icon(
                                Icons.keyboard_arrow_down_rounded,
                                color: textSecondary,
                                size: 18,
                              ),
                            ],
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
                              onPressed: widget.onNotifications == null
                                  ? null
                                  : () async {
                                      await widget.onNotifications!(
                                        bellContext,
                                      );
                                      _loadData();
                                    },
                              tooltip: 'Thông báo sự cố & bàn giao ca',
                              icon: Icon(
                                Icons.notifications_none_rounded,
                                color: textPrimary,
                                size: 26,
                              ),
                            ),
                          ),
                          if (_unreadHandoverIncidents > 0)
                            Positioned(
                              right: 6,
                              top: 6,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 5,
                                  vertical: 1.5,
                                ),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFEF4444),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                    color: bgColor,
                                    width: 1.5,
                                  ),
                                ),
                                constraints: const BoxConstraints(
                                  minWidth: 17,
                                  minHeight: 17,
                                ),
                                child: Text(
                                  '$_unreadHandoverIncidents',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.w800,
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

                // =========================================================
                // 2. RẠP VÀ CA LÀM VIỆC (Figma 34:2 - 385x102, radius 20)
                // =========================================================
                Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(20),
                    border: isLight
                        ? null
                        : Border.all(color: CSAppColors.border),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF0F172A).withValues(
                          alpha: isLight ? 0.04 : 0.2,
                        ),
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'CGV Vinh Trung Plaza',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: textPrimary,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 5,
                            ),
                            decoration: BoxDecoration(
                              color: isLight
                                  ? _statusGreenBg
                                  : _statusGreenDot.withValues(alpha: 0.16),
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.circle,
                                  color: _statusGreenDot,
                                  size: 6.5,
                                ),
                                const SizedBox(width: 5),
                                Text(
                                  'Đang hoạt động',
                                  style: TextStyle(
                                    color: isLight
                                        ? _statusGreen
                                        : const Color(0xFF34D399),
                                    fontSize: 11.8,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        height: 36,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        decoration: BoxDecoration(
                          color: isLight
                              ? const Color(0xFFF1F4FA)
                              : CSAppColors.surfaceStrong,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.access_time_filled_rounded,
                              color: isLight
                                  ? const Color(0xFF475569)
                                  : textSecondary,
                              size: 15,
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              flex: 6,
                              child: Text(
                                shiftLabel,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: textPrimary,
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                            Container(
                              width: 1,
                              height: 16,
                              margin: const EdgeInsets.symmetric(
                                horizontal: 12,
                              ),
                              color: isLight
                                  ? const Color(0xFFCBD5E1)
                                  : CSAppColors.border,
                            ),
                            Icon(
                              Icons.theaters_rounded,
                              color: isLight
                                  ? const Color(0xFF475569)
                                  : textSecondary,
                              size: 15,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              '$_activeRooms/$_activeRooms phòng',
                              style: TextStyle(
                                color: textPrimary,
                                fontSize: 12.5,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 8),

                // =========================================================
                // 3. CỤM THẺ TRUY CẬP NHANH 3D POP-OUT (Figma 52:233)
                // =========================================================
                SizedBox(
                  height: 168,
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    clipBehavior: Clip.none,
                    padding: const EdgeInsets.only(top: 32, bottom: 24),
                    child: Row(
                      children: [
                        _build3DQuickCard(
                          title: 'Suất Chiếu',
                          subtitle: '$_totalTodayShowtimes suất',
                          assetPath: 'assets/images/qa_showtimes.png',
                          gradientColors: const [
                            Color(0xFFFF354F),
                            Color(0xFFFF8795),
                          ],
                          shadowColor: const Color(
                            0xFFFF354F,
                          ).withValues(alpha: 0.28),
                          textColor: Colors.white,
                          imageTop: -28,
                          imageRight: 2,
                          imageWidth: 114,
                          imageHeight: 118,
                          onTap: widget.onShowtimes,
                        ),
                        const SizedBox(width: 11),
                        _build3DQuickCard(
                          title: 'Phòng Chiếu',
                          subtitle: '$_activeRooms phòng',
                          assetPath: 'assets/images/qa_rooms.png',
                          gradientColors: const [
                            Color(0xFF7C7876),
                            Color(0xFFC5BFC0),
                          ],
                          shadowColor: const Color(
                            0xFFCFC5C5,
                          ).withValues(alpha: isLight ? 0.70 : 0.25),
                          textColor: Colors.white,
                          imageTop: -28,
                          imageRight: -2,
                          imageWidth: 118,
                          imageHeight: 110,
                          onTap: widget.onRooms,
                        ),
                        const SizedBox(width: 11),
                        _build3DQuickCard(
                          title: 'Bàn Giao',
                          subtitle: _unreadHandoverIncidents > 0
                              ? '$_unreadHandoverIncidents sự cố'
                              : 'trống',
                          assetPath: 'assets/images/qa_handover.png',
                          gradientColors: const [
                            Color(0xFF0028FD),
                            Color(0xFF6B9FF8),
                          ],
                          shadowColor: const Color(
                            0xFF9CA8E5,
                          ).withValues(alpha: isLight ? 0.75 : 0.30),
                          textColor: Colors.white,
                          imageTop: -28,
                          imageRight: 4,
                          imageWidth: 106,
                          imageHeight: 118,
                          onTap: widget.onHandover,
                        ),
                        const SizedBox(width: 11),
                        _build3DQuickCard(
                          title: 'Lịch sử quét',
                          subtitle: '$_totalTodayShowtimes suất',
                          assetPath: 'assets/images/qa_history.png',
                          gradientColors: const [
                            Color(0xFFFFB40A),
                            Color(0xFFFFDE8A),
                          ],
                          shadowColor: const Color(
                            0xFFFBCC9E,
                          ).withValues(alpha: isLight ? 0.75 : 0.28),
                          textColor: Colors.white,
                          imageTop: -28,
                          imageRight: -4,
                          imageWidth: 124,
                          imageHeight: 116,
                          onTap: widget.onHistory,
                        ),
                      ],
                    ),
                  ),
                ),

                // =========================================================
                // 4. DANH SÁCH CÁC SUẤT GẦN NHẤT (Figma 34:2)
                // =========================================================
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Các suất gần nhất',
                      style: TextStyle(
                        fontSize: 17.3,
                        fontWeight: FontWeight.w600,
                        color: textPrimary,
                      ),
                    ),
                    InkWell(
                      onTap: widget.onShowtimes,
                      borderRadius: BorderRadius.circular(8),
                      child: const Padding(
                        padding: EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 4,
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Xem tất cả',
                              style: TextStyle(
                                fontSize: 12.7,
                                color: _brandBlue,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            SizedBox(width: 5),
                            Icon(
                              Icons.arrow_forward_rounded,
                              size: 14,
                              color: _brandBlue,
                            ),
                          ],
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
                      child: CircularProgressIndicator(color: _brandBlue),
                    ),
                  )
                else if (_recentShowtimes.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: cardColor,
                      borderRadius: BorderRadius.circular(18),
                      border: isLight
                          ? null
                          : Border.all(color: CSAppColors.border),
                    ),
                    child: Center(
                      child: Text(
                        'Hôm nay chưa có suất chiếu nào được lên lịch.',
                        style: TextStyle(color: textSecondary, fontSize: 13),
                      ),
                    ),
                  )
                else
                  ..._recentShowtimes.map((s) {
                    final movieName =
                        (s['movie_name'] ?? s['title'] ?? 'Tên phim')
                            .toString();
                    final startTime = (s['start_time'] ?? '').toString();
                    final endTime = (s['end_time'] ?? '').toString();
                    final roomName = formatRoomName(
                      (s['room_id'] ?? '').toString(),
                    );
                    final posterPath = (s['poster_path'] ?? '').toString();

                    final priority = _getShowtimePriority(s, now);
                    final isScreening = priority == 0;
                    final isUpcoming = priority == 1;
                    final isActiveShow = isScreening || isUpcoming;

                    final String assignText = isActiveShow
                        ? 'Đã phân công: 1/2'
                        : 'Đã kết thúc ca';
                    final Color assignColor = isActiveShow
                        ? (isLight ? _statusGreen : const Color(0xFF34D399))
                        : textSecondary;
                    final Color assignBg = isActiveShow
                        ? (isLight
                              ? const Color(0xFFE8F3ED)
                              : _statusGreenDot.withValues(alpha: 0.16))
                        : CSAppColors.surfaceStrong;

                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      decoration: BoxDecoration(
                        // Hiệu ứng viền trái xanh lá (INNER_SHADOW #13843B x=3.0 trong Figma)
                        color: isActiveShow ? _statusGreen : cardColor,
                        borderRadius: BorderRadius.circular(18),
                        border: (!isLight && !isActiveShow)
                            ? Border.all(color: CSAppColors.border)
                            : null,
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF0F172A).withValues(
                              alpha: isLight ? 0.04 : 0.2,
                            ),
                            blurRadius: 12,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      padding: EdgeInsets.only(left: isActiveShow ? 3.2 : 0),
                      child: Container(
                        decoration: BoxDecoration(
                          color: cardColor,
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              if (widget.onMovieSelected != null) {
                                widget.onMovieSelected!(s);
                              } else if (widget.onShowtimes != null) {
                                widget.onShowtimes!();
                              }
                            },
                            borderRadius: BorderRadius.circular(18),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 11,
                              ),
                              child: Row(
                                children: [
                                  // Áp phích phim (55x70, radius 10)
                                  ClipRRect(
                                    borderRadius: BorderRadius.circular(10),
                                    child: Container(
                                      width: 55,
                                      height: 70,
                                      color: CSAppColors.surfaceStrong,
                                      child: posterPath.isNotEmpty
                                          ? Image.network(
                                              'https://image.tmdb.org/t/p/w200$posterPath',
                                              fit: BoxFit.cover,
                                              errorBuilder:
                                                  (
                                                    context,
                                                    error,
                                                    stackTrace,
                                                  ) => Icon(
                                                    Icons.movie_outlined,
                                                    color: textSecondary,
                                                    size: 26,
                                                  ),
                                            )
                                          : Icon(
                                              Icons.movie_outlined,
                                              color: textSecondary,
                                              size: 26,
                                            ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),

                                  // Thông tin suất chiếu
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          movieName,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(
                                            fontSize: 14.8,
                                            fontWeight: FontWeight.w600,
                                            color: textPrimary,
                                          ),
                                        ),
                                        const SizedBox(height: 5),
                                        Row(
                                          children: [
                                            Icon(
                                              Icons.access_time_rounded,
                                              size: 13,
                                              color: textSecondary,
                                            ),
                                            const SizedBox(width: 4),
                                            Text(
                                              '$startTime - $endTime',
                                              style: TextStyle(
                                                fontSize: 12.5,
                                                color: textSecondary,
                                                fontWeight: FontWeight.w400,
                                              ),
                                            ),
                                            Container(
                                              width: 1,
                                              height: 13,
                                              margin:
                                                  const EdgeInsets.symmetric(
                                                    horizontal: 8,
                                                  ),
                                              color: textSecondary,
                                            ),
                                            Expanded(
                                              child: Text(
                                                roomName,
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: TextStyle(
                                                  fontSize: 12.5,
                                                  color: textSecondary,
                                                  fontWeight: FontWeight.w400,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 8,
                                            vertical: 3.5,
                                          ),
                                          decoration: BoxDecoration(
                                            color: assignBg,
                                            borderRadius: BorderRadius.circular(
                                              7,
                                            ),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(
                                                Icons.circle,
                                                color: assignColor,
                                                size: 6,
                                              ),
                                              const SizedBox(width: 5),
                                              Text(
                                                assignText,
                                                style: TextStyle(
                                                  fontSize: 11.2,
                                                  fontWeight: FontWeight.w600,
                                                  color: assignColor,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),

                                  Icon(
                                    Icons.chevron_right_rounded,
                                    color: textSecondary,
                                    size: 20,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Thẻ Truy cập nhanh 3D Pop-out chuẩn Figma (node 52:233)
  Widget _build3DQuickCard({
    required String title,
    required String subtitle,
    required String assetPath,
    required List<Color> gradientColors,
    required Color shadowColor,
    required Color textColor,
    required double imageTop,
    required double imageRight,
    required double imageWidth,
    required double imageHeight,
    required VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: 120,
        height: 109,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            // Nền thẻ Gradient bo góc 20px + Đổ bóng màu tương ứng
            Container(
              width: 120,
              height: 109,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: gradientColors,
                ),
                boxShadow: [
                  BoxShadow(
                    color: shadowColor,
                    blurRadius: 24,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
            ),

            // Minh họa 3D nổi vượt khung phía trên
            Positioned(
              top: imageTop,
              right: imageRight,
              child: IgnorePointer(
                child: Image.asset(
                  assetPath,
                  width: imageWidth,
                  height: imageHeight,
                  fit: BoxFit.contain,
                ),
              ),
            ),

            // Chữ tiêu đề & số liệu ở nửa dưới thẻ
            Positioned(
              left: 10,
              right: 6,
              bottom: 10,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 15.5,
                      fontWeight: FontWeight.w700,
                      color: textColor,
                      height: 1.15,
                      letterSpacing: -0.2,
                      shadows: [
                        Shadow(
                          color: Colors.black.withValues(alpha: 0.18),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    subtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 14.5,
                      fontWeight: FontWeight.w400,
                      color: textColor.withValues(alpha: 0.95),
                      height: 1.15,
                      shadows: [
                        Shadow(
                          color: Colors.black.withValues(alpha: 0.16),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
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
    );
  }
}
