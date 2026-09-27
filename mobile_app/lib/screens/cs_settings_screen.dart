

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';



import '../widgets/cs_status_tag.dart';



class CSSettingsScreen extends StatefulWidget {

  final ValueChanged<int>? onNavigationChanged;

  final VoidCallback? onNotifications;

  final VoidCallback? onChangePassword;

  final VoidCallback? onLogout;



  const CSSettingsScreen({

    super.key,

    this.onNavigationChanged,

    this.onNotifications,

    this.onChangePassword,

    this.onLogout,

  });



  @override

  State<CSSettingsScreen> createState() =>

      _CSSettingsScreenState();

}



class _CSSettingsScreenState extends State<CSSettingsScreen> {

  bool _soundEnabled = true;

  bool _offlineEnabled = false;



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      

      body: SafeArea(

        child: ListView(

          children: [

            Container(

              padding: const EdgeInsets.symmetric(vertical: 22),

              color: CSAppColors.surface,

              child: const Column(

                children: [

                  CircleAvatar(

                    radius: 34,

                    backgroundColor: CSAppColors.surfaceStrong,

                    child: Icon(Icons.person_outline, size: 34),

                  ),

                  SizedBox(height: 10),

                  Text(

                    CSMockData.employeeName,

                    style: TextStyle(

                      fontSize: 17,

                      fontWeight: FontWeight.w700,

                    ),

                  ),

                  Text(

                    '${CSMockData.employeeRole} · ${CSMockData.employeeId}',

                    style: TextStyle(

                      color: CSAppColors.muted,

                      fontSize: 11,

                    ),

                  ),

                  SizedBox(height: 5),

                  CSStatusTag(

                    text: '● ĐANG TRONG CA',

                    color: CSAppColors.success,

                  ),

                ],

              ),

            ),

            const CSSettingsSectionTitle('CẤU HÌNH VẬN HÀNH'),

            CSSettingsSwitchTile(

              icon: Icons.volume_up_outlined,

              title: 'Âm thanh & Rung khi quét',

              value: _soundEnabled,

              onChanged: (value) {

                setState(() => _soundEnabled = value);

              },

            ),

            CSSettingsSwitchTile(

              icon: Icons.wifi_off,

              title: 'Chế độ ngoại tuyến',

              value: _offlineEnabled,

              onChanged: (value) {

                setState(() => _offlineEnabled = value);

              },

            ),

            const CSSettingsTile(

              icon: Icons.sync,

              title: 'Đồng bộ dữ liệu vé',

              subtitle: 'Tự động đồng bộ mỗi 5 phút',

              trailing: 'Đã đồng bộ',

            ),

            const CSSettingsSectionTitle('HỆ THỐNG & BẢO MẬT'),

            CSSettingsTile(

              icon: Icons.notifications_none,

              title: 'Thông báo & Cảnh báo',

              onTap: widget.onNotifications,

            ),

            CSSettingsTile(

              icon: Icons.lock_outline,

              title: 'Đổi mật khẩu & Bảo mật',

              onTap: widget.onChangePassword,

            ),

            CSSettingsTile(

              icon: Icons.logout,

              title: 'Đăng xuất tài khoản',

              danger: true,

              onTap: widget.onLogout,

            ),

          ],

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

      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),

      child: Text(

        text,

        style: const TextStyle(

          color: CSAppColors.muted,

          fontSize: 10,

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

  final VoidCallback? onTap;



  const CSSettingsTile({

    super.key,

    required this.icon,

    required this.title,

    this.subtitle,

    this.trailing,

    this.danger = false,

    this.onTap,

  });



  @override

  Widget build(BuildContext context) {

    return Card(

      margin: const EdgeInsets.fromLTRB(10, 0, 10, 8),

      color: CSAppColors.surface,

      child: ListTile(

        onTap: onTap,

        leading: Icon(

          icon,

          color: danger

              ? CSAppColors.danger

              : CSAppColors.primary,

        ),

        title: Text(

          title,

          style: TextStyle(

            color: danger ? CSAppColors.danger : Colors.white,

          ),

        ),

        subtitle: subtitle == null

            ? null

            : Text(

                subtitle!,

                style: const TextStyle(

                  color: CSAppColors.muted,

                  fontSize: 10,

                ),

              ),

        trailing: trailing == null

            ? const Icon(Icons.chevron_right)

            : Text(

                trailing!,

                style: const TextStyle(

                  color: CSAppColors.muted,

                  fontSize: 10,

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

  final ValueChanged<bool> onChanged;



  const CSSettingsSwitchTile({

    super.key,

    required this.icon,

    required this.title,

    required this.value,

    required this.onChanged,

  });



  @override

  Widget build(BuildContext context) {

    return Card(

      margin: const EdgeInsets.fromLTRB(10, 0, 10, 8),

      color: CSAppColors.surface,

      child: SwitchListTile(

        secondary: Icon(icon, color: CSAppColors.primary),

        title: Text(title),

        value: value,

        onChanged: onChanged,

      ),

    );

  }

}

