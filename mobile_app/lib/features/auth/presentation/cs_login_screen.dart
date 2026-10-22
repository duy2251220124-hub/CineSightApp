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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),

          child: Column(
            children: [
              const Spacer(flex: 2),

              RichText(
                text: const TextSpan(
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),

                  children: [
                    TextSpan(text: 'Cine'),

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
                  'Đang nhập để tiếp tục',

                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
                ),
              ),

              const Align(
                alignment: Alignment.centerLeft,

                child: Text(
                  'Nhân viên rạp chiếu phim CineSight',

                  style: TextStyle(color: CSAppColors.muted),
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
                      setState(() => _hidePassword = !_hidePassword);
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
                          content: Text(ApiClient.lastLoginError ?? 'Lỗi đăng nhập'),
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

              const Text(
                'Gợi ý: hhh (MK: 12345) · duy (MK: 123)',
                style: TextStyle(color: CSAppColors.muted, fontSize: 11),
              ),

              const SizedBox(height: 18),
            ],
          ),
        ),
      ),
    );
  }
}
