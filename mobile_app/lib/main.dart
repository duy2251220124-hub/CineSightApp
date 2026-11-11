import 'package:flutter/material.dart';

import 'core/database/hive_service.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/features/auth/presentation/cs_login_screen.dart';
import 'features/home/presentation/home_screen.dart';

void main() async {
  // Bắt buộc gọi dòng này khi hàm main() có dùng async/await
  WidgetsFlutterBinding.ensureInitialized();

  // Khởi tạo Database Offline (Hive) ngay từ lúc vừa bật App
  await HiveService.init();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: HiveService.lightModeNotifier,
      builder: (context, isLight, _) {
        return MaterialApp(
          title: 'CineSight',
          debugShowCheckedModeBanner: false,
          // Dùng theme động (Light/Dark) cho toàn bộ các màn hình sau đăng nhập;
          // riêng CSLoginScreen được khóa cứng vào AppTheme.dark để giữ nguyên thiết kế gốc.
          theme: isLight ? CSAppTheme.light : AppTheme.dark,
          home: Builder(
            builder: (ctx) => CSLoginScreen(
              onLogin: () {
                Navigator.pushReplacement(
                  ctx,
                  MaterialPageRoute(builder: (_) => const HomeShell()),
                );
              },
            ),
          ),
        );
      },
    );
  }
}
