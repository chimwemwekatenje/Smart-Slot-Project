import 'package:flutter/material.dart';

class AppColors {
  static const background = Color(0xFF0F172A);
  static const surface = Color(0xFF1E2937);
  static const border = Color(0xFF334155);
  static const primary = Color(0xFF14B8A6);
  static const primaryDark = Color(0xFF0F766E);
  static const textPrimary = Color(0xFFE2E8F0);
  static const textMuted = Color(0xFF94A3B8);
  static const error = Color(0xFFEF4444);
  static const success = Color(0xFF22C55E);
  static const warning = Color(0xFFF59E0B);
}

final appTheme = ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: AppColors.background,
  colorScheme: const ColorScheme.dark(
    primary: AppColors.primary,
    secondary: AppColors.primary,
    surface: AppColors.surface,
    error: AppColors.error,
    onPrimary: Colors.white,
    onSurface: AppColors.textPrimary,
  ),
  fontFamily: 'sans-serif',
  appBarTheme: const AppBarTheme(
    backgroundColor: AppColors.surface,
    foregroundColor: AppColors.textPrimary,
    elevation: 0,
    titleTextStyle: TextStyle(
      color: AppColors.primary,
      fontSize: 20,
      fontWeight: FontWeight.bold,
    ),
  ),
  cardTheme: CardThemeData(
    color: AppColors.surface,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12),
      side: const BorderSide(color: AppColors.border),
    ),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.primary,
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: AppColors.primary,
      side: const BorderSide(color: AppColors.primary),
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.surface,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: AppColors.border),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: AppColors.border),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(8),
      borderSide: const BorderSide(color: AppColors.primary, width: 2),
    ),
    labelStyle: const TextStyle(color: AppColors.textMuted),
    hintStyle: const TextStyle(color: AppColors.textMuted),
  ),
  dividerColor: AppColors.border,
  textTheme: const TextTheme(
    headlineLarge: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
    headlineMedium: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold),
    titleLarge: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
    titleMedium: TextStyle(color: AppColors.textPrimary),
    bodyLarge: TextStyle(color: AppColors.textPrimary),
    bodyMedium: TextStyle(color: AppColors.textMuted),
    labelLarge: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
  ),
  bottomNavigationBarTheme: const BottomNavigationBarThemeData(
    backgroundColor: AppColors.surface,
    selectedItemColor: AppColors.primary,
    unselectedItemColor: AppColors.textMuted,
    type: BottomNavigationBarType.fixed,
  ),
  chipTheme: ChipThemeData(
    backgroundColor: AppColors.border,
    labelStyle: const TextStyle(color: AppColors.textPrimary, fontSize: 12),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
  ),
);
