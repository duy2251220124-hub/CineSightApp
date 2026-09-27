

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_primary_button.dart';



class CSLoginScreen extends StatefulWidget {

  final VoidCallback? onLogin;

  final VoidCallback? onForgotPassword;



  const CSLoginScreen({

    super.key,

    this.onLogin,

    this.onForgotPassword,

  });



  @override

  State<CSLoginScreen> createState() => _CSLoginScreenState();

}



class _CSLoginScreenState extends State<CSLoginScreen> {

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

                  style: TextStyle(

                    fontSize: 28,

                    fontWeight: FontWeight.w800,

                  ),

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

                  'Đăng nhập',

                  style: TextStyle(

                    fontSize: 22,

                    fontWeight: FontWeight.w700,

                  ),

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

              const TextField(

                decoration: InputDecoration(

                  prefixIcon: Icon(Icons.person_outline),

                  hintText: 'Mã nhân viên / Username',

                ),

              ),

              const SizedBox(height: 16),

              TextField(

                obscureText: _hidePassword,

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

              CSPrimaryButton(

                label: 'Đăng nhập',

                onPressed: widget.onLogin,

              ),

              TextButton(

                onPressed: widget.onForgotPassword,

                child: const Text('Quên mật khẩu?'),

              ),

              const Spacer(flex: 3),

              Text(

                '${CSMockData.employeeRole} · ${CSMockData.employeeId}',

                style: const TextStyle(

                  color: CSAppColors.muted,

                  fontSize: 10,

                ),

              ),

              const SizedBox(height: 18),

            ],

          ),

        ),

      ),

    );

  }

}

