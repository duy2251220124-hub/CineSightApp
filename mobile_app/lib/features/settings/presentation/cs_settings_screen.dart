import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_app/core/database/hive_service.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';

class CSSettingsScreen extends StatefulWidget {
  final ValueChanged<int>? onNavigationChanged;
  final VoidCallback? onNotifications;
  final VoidCallback? onSyncOffline;
  final VoidCallback? onChangePassword;
  final VoidCallback? onLogout;

  const CSSettingsScreen({
    super.key,
    this.onNavigationChanged,
    this.onNotifications,
    this.onSyncOffline,
    this.onChangePassword,
    this.onLogout,
  });

  @override
  State<CSSettingsScreen> createState() => _CSSettingsScreenState();
}

class _CSSettingsScreenState extends State<CSSettingsScreen> {
  bool _soundEnabled = true;
  bool _offlineEnabled = false;
  Uint8List? _avatarBytes;
  final ImagePicker _picker = ImagePicker();

  static const Color _iconBlue = Color(0xFF3B82F6);
  static const Color _cameraBadgeBlue = Color(0xFF2464F6);
  static const Color _statusGreen = Color(0xFF10B981);
  static const Color _dangerRed = Color(0xFFEF4444);

  String get _userKey {
    final u = ApiClient.currentUser;
    return (u?['username'] ?? u?['id']?.toString() ?? 'default_staff')
        .toString();
  }

  @override
  void initState() {
    super.initState();
    _loadSavedAvatar();
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

  Future<void> _pickAndSaveAvatar(ImageSource source) async {
    try {
      final XFile? picked = await _picker.pickImage(
        source: source,
        maxWidth: 512,
        maxHeight: 512,
        imageQuality: 85,
      );
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      if (bytes.isEmpty) return;

      final b64 = base64Encode(bytes);
      await HiveService.setEmployeeAvatar(_userKey, b64);
      if (!mounted) return;
      setState(() {
        _avatarBytes = bytes;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã cập nhật ảnh đại diện nhân viên!'),
          backgroundColor: _statusGreen,
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Không thể tải ảnh lên: $e'),
          backgroundColor: _dangerRed,
        ),
      );
    }
  }

  void _showAvatarPickerSheet() {
    final bool isLight = CSAppColors.isLight;
    final Color sheetBg = CSAppColors.surface;
    final Color tileBg = CSAppColors.surfaceStrong;
    final Color textHeader = CSAppColors.textPrimary;

    showModalBottomSheet(
      context: context,
      backgroundColor: sheetBg,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetCtx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: CSAppColors.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Cập nhật ảnh đại diện nhân viên',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: textHeader,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Ảnh đại diện sẽ được đồng bộ hiển thị trên cả Trang chủ và Hồ sơ ca trực',
                  style: TextStyle(fontSize: 12.5, color: CSAppColors.muted),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                ListTile(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  tileColor: tileBg,
                  leading: const Icon(
                    Icons.photo_library_rounded,
                    color: _cameraBadgeBlue,
                  ),
                  title: Text(
                    'Chọn ảnh từ thư viện',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: textHeader,
                      fontSize: 14,
                    ),
                  ),
                  onTap: () {
                    Navigator.pop(sheetCtx);
                    _pickAndSaveAvatar(ImageSource.gallery);
                  },
                ),
                const SizedBox(height: 10),
                ListTile(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  tileColor: tileBg,
                  leading: const Icon(
                    Icons.photo_camera_rounded,
                    color: Color(0xFF7C3AED),
                  ),
                  title: Text(
                    'Chụp ảnh mới bằng Camera',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: textHeader,
                      fontSize: 14,
                    ),
                  ),
                  onTap: () {
                    Navigator.pop(sheetCtx);
                    _pickAndSaveAvatar(ImageSource.camera);
                  },
                ),
                if (_avatarBytes != null) ...[
                  const SizedBox(height: 10),
                  ListTile(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    tileColor: isLight
                        ? const Color(0xFFFEF2F2)
                        : _dangerRed.withValues(alpha: 0.14),
                    leading: const Icon(
                      Icons.delete_outline_rounded,
                      color: _dangerRed,
                    ),
                    title: const Text(
                      'Gỡ ảnh hiện tại',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: _dangerRed,
                        fontSize: 14,
                      ),
                    ),
                    onTap: () async {
                      Navigator.pop(sheetCtx);
                      await HiveService.setEmployeeAvatar(_userKey, null);
                      if (!mounted) return;
                      setState(() => _avatarBytes = null);
                    },
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    _loadSavedAvatar();
    final bool isLight = CSAppColors.isLight;
    final Color bgColor = CSAppColors.background;
    final Color cardColor = CSAppColors.surface;
    final Color textHeader = CSAppColors.textPrimary;
    final Color textMuted = CSAppColors.muted;

    final userName =
        (ApiClient.currentUser?['name'] ?? 'Phạm Ngọc Linh').toString();
    final userRole = (ApiClient.currentUser?['role'] ?? 'Soát vé').toString();
    final userCode =
        (ApiClient.currentUser?['username'] ?? 'USER').toString().toUpperCase();

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: (isLight ? SystemUiOverlayStyle.dark : SystemUiOverlayStyle.light)
          .copyWith(statusBarColor: Colors.transparent),
      child: Scaffold(
        backgroundColor: bgColor,
        body: SafeArea(
          bottom: false,
          child: ListView(
            padding: const EdgeInsets.only(bottom: 110),
            children: [
              // =========================================================
              // 1. PROFILE HEADER (Figma node 33:250 - 390x183)
              // Nút thay đổi ảnh đại diện nhân viên đặt tại đây
              // =========================================================
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 20),
                decoration: BoxDecoration(
                  color: cardColor,
                  border: isLight
                      ? null
                      : Border(bottom: BorderSide(color: CSAppColors.border)),
                ),
                child: Column(
                  children: [
                    // Group 2 (82x80): Ảnh đại diện bo góc 25px + nút Camera xanh #2464F6
                    GestureDetector(
                      onTap: _showAvatarPickerSheet,
                      child: SizedBox(
                        width: 86,
                        height: 84,
                        child: Stack(
                          clipBehavior: Clip.none,
                          children: [
                            Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(25),
                                color: isLight
                                    ? const Color(0xFFDBEAFE)
                                    : _cameraBadgeBlue.withValues(alpha: 0.2),
                                border: Border.all(
                                  color: isLight
                                      ? Colors.white
                                      : const Color(0xFF2B3851),
                                  width: 2,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: const Color(0xFF0F172A).withValues(
                                      alpha: isLight ? 0.08 : 0.3,
                                    ),
                                    blurRadius: 12,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(23),
                                child: _avatarBytes != null
                                    ? Image.memory(
                                        _avatarBytes!,
                                        width: 80,
                                        height: 80,
                                        fit: BoxFit.cover,
                                      )
                                    : const Icon(
                                        Icons.person_rounded,
                                        size: 42,
                                        color: _cameraBadgeBlue,
                                      ),
                              ),
                            ),
                            Positioned(
                              right: 0,
                              bottom: 0,
                              child: Container(
                                width: 28,
                                height: 29,
                                decoration: BoxDecoration(
                                  color: _cameraBadgeBlue,
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: cardColor,
                                    width: 2,
                                  ),
                                ),
                                child: const Icon(
                                  Icons.camera_alt_outlined,
                                  color: Colors.white,
                                  size: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      userName,
                      style: TextStyle(
                        fontSize: 17.3,
                        fontWeight: FontWeight.w500,
                        color: textHeader,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '$userRole · $userCode',
                      style: TextStyle(
                        color: textMuted,
                        fontSize: 13,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    const SizedBox(height: 6),
                    // Badge "ĐANG TRONG CA" (node 33:255)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: _statusGreen.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.circle, color: _statusGreen, size: 6),
                          SizedBox(width: 6),
                          Text(
                            'ĐANG TRONG CA',
                            style: TextStyle(
                              color: _statusGreen,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // =========================================================
              // 2. OPTIONS LIST (Figma node 33:258)
              // =========================================================
              const CSSettingsSectionTitle('CẤU HÌNH VẬN HÀNH'),

              // Nút bật/tắt chế độ Light Mode / Dark Mode
              CSSettingsSwitchTile(
                icon: isLight
                    ? Icons.light_mode_outlined
                    : Icons.dark_mode_outlined,
                title: 'Giao diện Sáng (Light Mode)',
                value: isLight,
                activeTrackColor: _iconBlue.withValues(alpha: 0.59),
                activeThumbColor: Colors.white,
                onChanged: (value) async {
                  await HiveService.setLightMode(value);
                  if (mounted) setState(() {});
                },
              ),

              CSSettingsSwitchTile(
                icon: Icons.volume_up_outlined,
                title: 'Âm thanh & Rung khi quét',
                value: _soundEnabled,
                activeTrackColor: _iconBlue.withValues(alpha: 0.59),
                activeThumbColor: Colors.white,
                onChanged: (value) {
                  setState(() => _soundEnabled = value);
                },
              ),

              CSSettingsSwitchTile(
                icon: Icons.wifi_off_outlined,
                title: 'Chế độ ngoại tuyến',
                value: _offlineEnabled,
                activeTrackColor: const Color(0xFF99BEFA),
                activeThumbColor: _iconBlue,
                onChanged: (value) {
                  setState(() => _offlineEnabled = value);
                },
              ),

              CSSettingsTile(
                icon: Icons.sync_rounded,
                title: 'Đồng bộ dữ liệu vé',
                subtitle: 'Tự động đồng bộ mỗi 5 phút',
                trailing: 'Đã đồng bộ',
                onTap: widget.onSyncOffline,
              ),

              const CSSettingsSectionTitle('HỆ THỐNG & BẢO MẬT'),

              CSSettingsTile(
                icon: Icons.notifications_none_rounded,
                title: 'Thông báo & Cảnh báo',
                onTap: widget.onNotifications,
              ),

              CSSettingsTile(
                icon: Icons.lock_outline_rounded,
                title: 'Đổi mật khẩu & Bảo mật',
                onTap: widget.onChangePassword,
              ),

              CSSettingsTile(
                icon: Icons.logout_rounded,
                title: 'Đăng xuất tài khoản',
                danger: true,
                showChevron: false,
                onTap: widget.onLogout,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class CSSettingsSectionTitle extends StatelessWidget {
  final String text;

  const CSSettingsSectionTitle(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 8),
      child: Text(
        text,
        style: TextStyle(
          color: CSAppColors.muted,
          fontSize: 12,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}

class CSSettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final String? trailing;
  final bool danger;
  final bool showChevron;
  final VoidCallback? onTap;

  const CSSettingsTile({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.danger = false,
    this.showChevron = true,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const Color iconBlue = Color(0xFF3B82F6);
    const Color dangerRed = Color(0xFFEF4444);
    final bool isLight = CSAppColors.isLight;
    final Color textDark = CSAppColors.textPrimary;
    final Color textSubtitle = CSAppColors.muted;
    final Color textTrailing = isLight
        ? const Color(0xFF94A3B8)
        : CSAppColors.muted;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 10),
      decoration: BoxDecoration(
        color: CSAppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: isLight ? null : Border.all(color: CSAppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: 16,
              vertical: subtitle != null ? 13 : 15,
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 20,
                  color: danger ? dangerRed : iconBlue,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: danger ? dangerRed : textDark,
                        ),
                      ),
                      if (subtitle != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          subtitle!,
                          style: TextStyle(
                            color: textSubtitle,
                            fontSize: 12,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                if (trailing != null)
                  Text(
                    trailing!,
                    style: TextStyle(
                      color: textTrailing,
                      fontSize: 13,
                      fontWeight: FontWeight.w400,
                    ),
                  )
                else if (showChevron)
                  Icon(
                    Icons.chevron_right_rounded,
                    color: textTrailing,
                    size: 20,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class CSSettingsSwitchTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final bool value;
  final Color activeTrackColor;
  final Color activeThumbColor;
  final ValueChanged<bool> onChanged;

  const CSSettingsSwitchTile({
    super.key,
    required this.icon,
    required this.title,
    required this.value,
    this.activeTrackColor = const Color(0x963B82F6),
    this.activeThumbColor = Colors.white,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final bool isLight = CSAppColors.isLight;
    return Container(
      height: 56,
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 10),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: CSAppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: isLight ? null : Border.all(color: CSAppColors.border),
      ),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF3B82F6), size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: CSAppColors.textPrimary,
              ),
            ),
          ),
          // Custom Pill Switch chuẩn thiết kế Figma (44x24, radius 12, handle 20x20)
          GestureDetector(
            onTap: () => onChanged(!value),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOutCubic,
              width: 44,
              height: 24,
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: value
                    ? activeTrackColor
                    : (isLight
                          ? const Color(0xFFCBD5E1)
                          : const Color(0xFF334155)),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: value ? Alignment.centerRight : Alignment.centerLeft,
              child: Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  color: value ? activeThumbColor : Colors.white,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.12),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
