import 'package:flutter/material.dart';

import 'features/scanner/presentation/scanner_screen.dart';

void main() {
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
