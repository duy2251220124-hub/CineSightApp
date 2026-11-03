import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/network/api_client.dart';

class CSLoginScreen extends StatefulWidget {
  final VoidCallback? onLogin;
  final VoidCallback? onForgotPassword;

  const CSLoginScreen({super.key, this.onLogin, this.onForgotPassword});

  @override
  State<CSLoginScreen> createState() => _CSLoginScreenState();
}

class _CSLoginScreenState extends State<CSLoginScreen> {
  final _userCtrl = TextEditingController(text: '');
  final _passCtrl = TextEditingController(text: '');
  bool _isLoading = false;
  bool _hidePassword = true;
  int _devTapCount = 0;

  // Màu nền tối sâu trích xuất trực tiếp từ nền gốc của tệp logo.png
  static const Color _logoDeepBg = Color(0xFF04070F);
  static const Color _screenBottomBg = Color(0xFF070B14);

  void _showServerSettingsDialog() {
    final urlCtrl = TextEditingController(text: ApiClient.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: CSAppColors.surface,
        title: const Row(
          children: [
            Icon(Icons.dns_outlined, color: CSAppColors.primary),
            SizedBox(width: 8),
            Text(
              'Cấu hình Server URL',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Nhập địa chỉ máy chủ AI / Backend (ví dụ link ngrok mới hoặc IP mạng LAN http://192.168.x.x:8000):',
              style: TextStyle(fontSize: 13, color: CSAppColors.muted),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: urlCtrl,
              autocorrect: false,
              enableSuggestions: false,
              style: const TextStyle(fontSize: 13),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.link),
                hintText:
                    'https://...ngrok-free.app hoặc http://192.168.1.x:8000',
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: () {
                urlCtrl.text = 'https://quill-device-deny.ngrok-free.dev';
              },
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text(
                'Khôi phục mặc định',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'Hủy',
              style: TextStyle(color: CSAppColors.muted),
            ),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: CSAppColors.primary,
              foregroundColor: Colors.white,
            ),
            onPressed: () {
              final newUrl = urlCtrl.text.trim();
              if (newUrl.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Vui lòng không để trống địa chỉ máy chủ!'),
                  ),
                );
                return;
              }
              ApiClient.updateBaseUrl(newUrl);
              Navigator.pop(ctx);
              setState(() {});
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Đã cập nhật máy chủ: $newUrl'),
                  backgroundColor: CSAppColors.success,
                ),
              );
            },
            child: const Text('Lưu máy chủ'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _logoDeepBg,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        // Lớp nền chuyển sắc mượt: nửa trên khớp tuyệt đối với nền đen xanh của logo.png
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.0, -0.48),
            radius: 0.95,
            colors: [
              const Color(0xFF0A1428).withValues(alpha: 0.65),
              _logoDeepBg,
              _screenBottomBg,
            ],
            stops: const [0.0, 0.45, 1.0],
          ),
        ),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                physics: const ClampingScrollPhysics(),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: IntrinsicHeight(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: Column(
                        children: [
                          const SizedBox(height: 8),
                          // Nút cài đặt nhanh Server URL ở góc trên bên phải
                          Align(
                            alignment: Alignment.centerRight,
                            child: IconButton(
                              onPressed: _showServerSettingsDialog,
                              tooltip: 'Cấu hình Server URL',
                              icon: Icon(
                                Icons.settings_outlined,
                                color: CSAppColors.muted.withValues(alpha: 0.6),
                                size: 20,
                              ),
                            ),
                          ),
                          const Spacer(),

                          // Cụm Logo hòa tan hoàn toàn vào nền màn hình
                          SizedBox(
                            width: 124,
                            height: 124,
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                // 1. Đốm sáng (Ambient Glow) đặt gọn sau tâm chữ C
                                Container(
                                  width: 48,
                                  height: 48,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(
                                        color: CSAppColors.primary.withValues(
                                          alpha: 0.38,
                                        ),
                                        blurRadius: 40,
                                        spreadRadius: 2,
                                      ),
                                    ],
                                  ),
                                ),
                                // 2. Mặt nạ Radial làm tan hoàn toàn 4 viền ảnh vào nền _logoDeepBg
                                ShaderMask(
                                  shaderCallback: (Rect bounds) {
                                    return const RadialGradient(
                                      center: Alignment.center,
                                      radius: 0.48,
                                      colors: [
                                        Colors.white,
                                        Colors.white,
                                        Color(0x99FFFFFF),
                                        Colors.transparent,
                                      ],
                                      stops: [0.0, 0.55, 0.80, 1.0],
                                    ).createShader(bounds);
                                  },
                                  blendMode: BlendMode.dstIn,
                                  child: Image.asset(
                                    'assets/images/logo.png',
                                    width: 124,
                                    height: 124,
                                    fit: BoxFit.contain,
                                    filterQuality: FilterQuality.high,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 6),

                          RichText(
                            text: const TextSpan(
                              style: TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.3,
                              ),
                              children: [
                                TextSpan(
                                  text: 'Cine',
                                  style: TextStyle(color: Colors.white),
                                ),
                                TextSpan(
                                  text: 'Sight',
                                  style: TextStyle(color: CSAppColors.primary),
                                ),
                              ],
                            ),
                          ),

                          const Spacer(),

                          const Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              'Đăng nhập',
                              style: TextStyle(
                                fontSize: 26,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              'Nhân viên rạp chiếu phim CineSight',
                              style: TextStyle(
                                color: CSAppColors.muted,
                                fontSize: 13,
                              ),
                            ),
                          ),

                          const SizedBox(height: 22),

                          TextField(
                            controller: _userCtrl,
                            textCapitalization: TextCapitalization.none,
                            autocorrect: false,
                            enableSuggestions: false,
                            decoration: const InputDecoration(
                              prefixIcon: Icon(Icons.person_outline),
                              hintText: 'Mã nhân viên / Username',
                            ),
                          ),

                          const SizedBox(height: 16),

                          TextField(
                            controller: _passCtrl,
                            obscureText: _hidePassword,
                            textCapitalization: TextCapitalization.none,
                            autocorrect: false,
                            enableSuggestions: false,
                            decoration: InputDecoration(
                              prefixIcon: const Icon(Icons.lock_outline),
                              hintText: 'Mật khẩu / PIN',
                              suffixIcon: IconButton(
                                onPressed: () {
                                  setState(
                                    () => _hidePassword = !_hidePassword,
                                  );
                                },
                                icon: Icon(
                                  _hidePassword
                                      ? Icons.visibility_outlined
                                      : Icons.visibility_off_outlined,
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 22),

                          if (_isLoading)
                            const CircularProgressIndicator()
                          else
                            CSPrimaryButton(
                              label: 'Đăng nhập',
                              onPressed: () async {
                                setState(() => _isLoading = true);
                                final success = await ApiClient.login(
                                  _userCtrl.text,
                                  _passCtrl.text,
                                );
                                setState(() => _isLoading = false);
                                if (!context.mounted) return;
                                if (success && widget.onLogin != null) {
                                  widget.onLogin!();
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        ApiClient.lastLoginError ??
                                            'Lỗi đăng nhập',
                                      ),
                                      backgroundColor: Colors.red.shade800,
                                    ),
                                  );
                                }
                              },
                            ),

                          TextButton(
                            onPressed: widget.onForgotPassword,
                            child: const Text('Quên mật khẩu?'),
                          ),

                          const Spacer(flex: 3),

                          GestureDetector(
                            onTap: () {
                              _devTapCount++;
                              if (_devTapCount >= 5) {
                                _devTapCount = 0;
                                _showServerSettingsDialog();
                              }
                            },
                            child: const Text(
                              'Phiên bản v2.4.1 (Production)',
                              style: TextStyle(
                                color: CSAppColors.muted,
                                fontSize: 12,
                              ),
                            ),
                          ),

                          const SizedBox(height: 14),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
