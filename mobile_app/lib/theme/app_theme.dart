

import 'package:flutter/material.dart';



abstract final class CSAppColors {

  static const background = Color(0xFF070B14);

  static const surface = Color(0xFF151D2E);

  static const surfaceStrong = Color(0xFF1C2538);

  static const border = Color(0xFF2B3851);

  static const primary = Color(0xFF2F72F4);

  static const success = Color(0xFF14C692);

  static const warning = Color(0xFFFFA000);

  static const danger = Color(0xFFFF414D);

  static const muted = Color(0xFF8590A5);

  static const foreground = Color(0xFFF7F9FC);

}



abstract final class CSAppTheme {

  static ThemeData get dark {

    return ThemeData(

      brightness: Brightness.dark,

      useMaterial3: true,

      scaffoldBackgroundColor: CSAppColors.background,

      colorScheme: const ColorScheme.dark(

        primary: CSAppColors.primary,

        surface: CSAppColors.surface,

        error: CSAppColors.danger,

      ),

      dividerColor: CSAppColors.border,

      inputDecorationTheme: InputDecorationTheme(

        filled: true,

        fillColor: CSAppColors.surfaceStrong,

        hintStyle: const TextStyle(

          color: CSAppColors.muted,

          fontSize: 13,

        ),

        border: OutlineInputBorder(

          borderRadius: BorderRadius.circular(9),

          borderSide: BorderSide.none,

        ),

      ),

    );

  }

}






