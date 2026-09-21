import 'package:flutter/material.dart';

import 'core/database/hive_service.dart';
import 'features/scanner/presentation/scanner_screen.dart';

void main() async {
  // Bắt buộc gọi dòng này khi hàm main() có dùng async/await (để khởi tạo các hàm Native của đt)
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
      title: 'CineSight Scanner',
      theme: ThemeData(
        // Rạp phim nên xài giao diện nền tối (Dark mode) cho chuyên nghiệp và đỡ chói mắt
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.red,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const ScannerScreen(),
    );
  }
}
