import 'package:flutter/material.dart';

import '../core/database/hive_service.dart';

abstract final class CSAppColors {
  static bool get isLight => HiveService.isLightMode;

  static Color get background =>
      isLight ? const Color(0xFFF1F4FA) : const Color(0xFF070B14);

  static Color get surface => isLight ? Colors.white : const Color(0xFF151D2E);

  static Color get surfaceStrong =>
      isLight ? const Color(0xFFF1F5F9) : const Color(0xFF1C2538);

  static Color get border =>
      isLight ? const Color(0xFFE2E8F0) : const Color(0xFF2B3851);

  static const primary = Color(0xFF2464F6);

  static const success = Color(0xFF14C692);

  static const warning = Color(0xFFFFA000);

  static const danger = Color(0xFFFF414D);

  static const darkSurface = Color(0xFF151D2E);
  static const darkMuted = Color(0xFF8590A5);

  static Color get muted => isLight ? const Color(0xFF64748B) : darkMuted;

  static Color get foreground =>
      isLight ? const Color(0xFF161D2D) : const Color(0xFFF7F9FC);

  static Color get textPrimary => foreground;

  static Color get textSecondary =>
      isLight ? const Color(0xFF475569) : Colors.white70;

  static Color get iconMuted =>
      isLight ? const Color(0xFF64748B) : Colors.white54;

  static Color get seatEmpty =>
      isLight ? const Color(0xFFCBD5E1) : const Color(0xFF1E293B);

  static Color get seatEmptyText =>
      isLight ? const Color(0xFF1E293B) : Colors.white;
}

abstract final class CSAppTheme {
  static ThemeData get current => CSAppColors.isLight ? light : dark;

  static ThemeData get light {
    return ThemeData(
      brightness: Brightness.light,
      useMaterial3: true,
      scaffoldBackgroundColor: const Color(0xFFF1F4FA),
      colorScheme: const ColorScheme.light(
        primary: CSAppColors.primary,
        surface: Colors.white,
        onSurface: Color(0xFF161D2D),
        error: CSAppColors.danger,
      ),
      dividerColor: const Color(0xFFE2E8F0),
      dialogTheme: const DialogThemeData(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF1F5F9),
        hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
        ),
      ),
    );
  }

  static ThemeData get dark {
    return ThemeData(
      brightness: Brightness.dark,
      useMaterial3: true,
      scaffoldBackgroundColor: const Color(0xFF070B14),
      colorScheme: const ColorScheme.dark(
        primary: CSAppColors.primary,
        surface: Color(0xFF151D2E),
        onSurface: Color(0xFFF7F9FC),
        error: CSAppColors.danger,
      ),
      dividerColor: const Color(0xFF2B3851),
      dialogTheme: const DialogThemeData(
        backgroundColor: Color(0xFF151D2E),
        surfaceTintColor: Colors.transparent,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Color(0xFF151D2E),
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1C2538),
        hintStyle: const TextStyle(color: Color(0xFF8590A5), fontSize: 13),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(9),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
