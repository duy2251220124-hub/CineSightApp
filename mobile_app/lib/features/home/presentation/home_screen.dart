import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_theme.dart';
import '../../scanner/presentation/scanner_screen.dart';

// ──────────────────────────────────────────────────────────
// HOME SCREEN + BOTTOM NAV — UI only, theo thiết kế Figma
// Dữ liệu trong file này là MOCK — đánh dấu TODO để nối sau
// ──────────────────────────────────────────────────────────

// ── Mock data ─────────────────────────────────────────────
// TODO: nối dữ liệu thật sau — lấy từ API / local store
const _mockShowtimes = [
  _MockShowtime(
    title: 'Kung Fu Panda 4',
    time: '19:30 - 21:20',
    room: 'Phòng 05',
    statusLabel: 'Đã phân công: 1/2',
    statusColor: AppColors.statusGreen,
  ),
  _MockShowtime(
    title: 'Dune: Part Two',
    time: '20:00 - 22:45',
    room: 'Phòng 01',
    statusLabel: 'Đã phân công: 1/1',
    statusColor: AppColors.statusOrange,
  ),
  _MockShowtime(
    title: 'Godzilla x Kong',
    time: '21:00 - 23:05',
    room: 'Phòng 03',
    statusLabel: 'Chưa phân công: 0/1',
    statusColor: AppColors.statusRed,
  ),
];

class _MockShowtime {
  final String title;
  final String time;
  final String room;
  final String statusLabel;
  final Color statusColor;
  const _MockShowtime({
    required this.title,
    required this.time,
    required this.room,
    required this.statusLabel,
    required this.statusColor,
  });
}

// ── Entry point: màn hình chứa BottomNav shell ─────────────
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _currentIndex = 0;

  // Danh sách màn hình ứng với từng tab
  // ScannerScreen giữ nguyên logic thật — chỉ gắn vào tab
  late final List<Widget> _tabs = [
    const _HomeTab(), // Trang chủ
    const ScannerScreen(), // Quét vé — GIỮ NGUYÊN LOGIC CŨ
    const _PlaceholderTab(label: 'Cảnh báo'), // TODO: nối dữ liệu thật sau
    const _PlaceholderTab(label: 'Cài đặt'), // TODO: nối dữ liệu thật sau
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: IndexedStack(index: _currentIndex, children: _tabs),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.border, width: 1)),
      ),
      child: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Trang chủ',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.qr_code_scanner_outlined),
            activeIcon: Icon(Icons.qr_code_scanner),
            label: 'Quét vé',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.notifications_outlined),
            activeIcon: Icon(Icons.notifications_rounded),
            label: 'Cảnh báo',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings_outlined),
            activeIcon: Icon(Icons.settings_rounded),
            label: 'Cài đặt',
          ),
        ],
      ),
    );
  }
}

// ── Tab Trang Chủ ──────────────────────────────────────────
class _HomeTab extends StatelessWidget {
  const _HomeTab();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 16),
            _buildHeader(),
            const SizedBox(height: 16),
            _buildShiftCard(),
            const SizedBox(height: 24),
            _buildQuickActions(),
            const SizedBox(height: 24),
            _buildShowtimeSection(),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  // ── Header: Avatar + tên + bell ─────────────────────────
  Widget _buildHeader() {
    return Row(
      children: [
        // Avatar = logo nhỏ
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: AppColors.cardBg,
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.asset('assets/images/logo.png', fit: BoxFit.cover),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // TODO: nối dữ liệu thật sau — lấy từ auth session
              Text(
                'Nguyen Van A',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                'Staff · Us-221033', // TODO: nối dữ liệu thật sau
                style: GoogleFonts.inter(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.cardBg,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.border),
          ),
          child: const Icon(
            Icons.notifications_outlined,
            color: AppColors.textSecondary,
            size: 20,
          ),
        ),
      ],
    );
  }

  // ── Card ca làm việc ─────────────────────────────────────
  Widget _buildShiftCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'CGV Vinh Trung Plaza', // TODO: nối dữ liệu thật sau
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: AppColors.statusGreen.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: AppColors.statusGreen,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      'ON SHIFT', // TODO: nối dữ liệu thật sau
                      style: GoogleFonts.inter(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppColors.statusGreen,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _shiftInfoRow(
            Icons.access_time_outlined,
            'Ca làm việc: 10:00 - 18:00', // TODO: nối dữ liệu thật sau
          ),
          const SizedBox(height: 6),
          _shiftInfoRow(
            Icons.home_outlined,
            'Rạp đang hoạt động: 5/5 phòng', // TODO: nối dữ liệu thật sau
          ),
        ],
      ),
    );
  }

  Widget _shiftInfoRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 14, color: AppColors.textSecondary),
        const SizedBox(width: 6),
        Text(
          text,
          style: GoogleFonts.inter(
            fontSize: 13,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  // ── 4 nút chức năng nhanh ────────────────────────────────
  Widget _buildQuickActions() {
    const actions = [
      _QuickAction(icon: Icons.movie_filter_outlined, label: 'Suất Chiếu'),
      _QuickAction(icon: Icons.videocam_outlined, label: 'Phòng Chiếu'),
      _QuickAction(icon: Icons.history_rounded, label: 'Lịch Sử Vé'),
      _QuickAction(icon: Icons.swap_horiz_rounded, label: 'Bàn giao ca'),
    ];

    return Row(
      children: actions.map((a) {
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: _buildActionButton(a),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildActionButton(_QuickAction action) {
    return GestureDetector(
      onTap: () {
        // TODO: nối dữ liệu thật sau — navigate theo action
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(action.icon, color: AppColors.primary, size: 26),
            const SizedBox(height: 8),
            Text(
              action.label,
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Danh sách suất gần nhất ──────────────────────────────
  Widget _buildShowtimeSection() {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Các suất gần nhất',
              style: GoogleFonts.inter(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            GestureDetector(
              onTap: () {
                // TODO: nối dữ liệu thật sau — navigate to showtime list
              },
              child: Text(
                'Xem tất cả',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: AppColors.primary,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ..._mockShowtimes.map(_buildShowtimeCard), // TODO: nối dữ liệu thật sau
      ],
    );
  }

  Widget _buildShowtimeCard(_MockShowtime s) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            // Thumbnail placeholder
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: AppColors.inputBg,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.movie_outlined,
                color: AppColors.textHint,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    s.title,
                    style: GoogleFonts.inter(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${s.time}  |  ${s.room}',
                    style: GoogleFonts.inter(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: s.statusColor,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        s.statusLabel,
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: s.statusColor,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right_rounded,
              color: AppColors.textSecondary,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}

// ── Quick action model ────────────────────────────────────
class _QuickAction {
  final IconData icon;
  final String label;
  const _QuickAction({required this.icon, required this.label});
}

// ── Placeholder tab cho màn hình chưa làm ────────────────
class _PlaceholderTab extends StatelessWidget {
  final String label;
  const _PlaceholderTab({required this.label});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        label,
        style: GoogleFonts.inter(color: AppColors.textSecondary, fontSize: 16),
      ),
    );
  }
}
