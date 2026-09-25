import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_theme.dart';

// ──────────────────────────────────────────────────────────
// LOGIN SCREEN — UI only, theo thiết kế Figma
// Chỉ render giao diện tĩnh, KHÔNG xử lý auth thật
// ──────────────────────────────────────────────────────────
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _obscurePassword = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              const SizedBox(height: 60),

              // ── LOGO ─────────────────────────────────────
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.35),
                      blurRadius: 24,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: Image.asset(
                    'assets/images/logo.png',
                    fit: BoxFit.cover,
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // ── TÊN APP ──────────────────────────────────
              RichText(
                text: TextSpan(
                  style: GoogleFonts.inter(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                  ),
                  children: const [
                    TextSpan(
                      text: 'Cine',
                      style: TextStyle(color: AppColors.textPrimary),
                    ),
                    TextSpan(
                      text: 'Sight',
                      style: TextStyle(color: AppColors.primary),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 48),

              // ── TIÊU ĐỀ ──────────────────────────────────
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Đăng nhập',
                  style: GoogleFonts.inter(
                    fontSize: 26,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),

              const SizedBox(height: 6),

              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Nhân viên rạp chiếu phim CineSight',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    color: AppColors.textSecondary,
                  ),
                ),
              ),

              const SizedBox(height: 32),

              // ── FIELD USERNAME ────────────────────────────
              TextFormField(
                // TODO: nối dữ liệu thật sau — controller của auth provider
                style: GoogleFonts.inter(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                ),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.person_outline_rounded, size: 20),
                  hintText: 'Mã nhân viên / Username',
                ),
              ),

              const SizedBox(height: 14),

              // ── FIELD PASSWORD ────────────────────────────
              TextFormField(
                // TODO: nối dữ liệu thật sau — controller của auth provider
                obscureText: _obscurePassword,
                style: GoogleFonts.inter(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                ),
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
                  hintText: 'Mật khẩu / PIN',
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                      size: 20,
                    ),
                    onPressed: () {
                      setState(() => _obscurePassword = !_obscurePassword);
                    },
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // ── NÚT ĐĂNG NHẬP ────────────────────────────
              ElevatedButton(
                onPressed: () {
                  // TODO: nối dữ liệu thật sau — gọi auth use case
                },
                child: Text(
                  'Đăng nhập',
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),

              const SizedBox(height: 18),

              // ── QUÊN MẬT KHẨU ────────────────────────────
              GestureDetector(
                onTap: () {
                  // TODO: nối dữ liệu thật sau — navigate to forgot password
                },
                child: Text(
                  'Quên mật khẩu?',
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppColors.primary,
                  ),
                ),
              ),

              const SizedBox(height: 60),

              // ── VERSION ───────────────────────────────────
              Text(
                'Phiên bản v2.4.1 (Production)',
                style: GoogleFonts.inter(
                  fontSize: 12,
                  color: AppColors.textHint,
                ),
              ),

              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
