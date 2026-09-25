import 'package:flutter/material.dart';

import 'core/database/hive_service.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';

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
    return MaterialApp(
      title: 'CineSight',
      debugShowCheckedModeBanner: false,
      // Dùng theme tập trung từ AppTheme — KHÔNG định nghĩa màu trực tiếp ở đây
      theme: AppTheme.dark,
      // TODO: nối dữ liệu thật sau — thay bằng go_router khi có auth logic
      // Hiện tại: bắt đầu từ LoginScreen để đúng luồng Figma
      home: const LoginScreen(),
    );
  }
}
