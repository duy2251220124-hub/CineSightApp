import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:mobile_app/theme/app_theme.dart';

class CSBottomNav extends StatefulWidget {
  final int selectedIndex;
  final ValueChanged<int>? onChanged;
  final int alertCount; // Số lượng cảnh báo AI đang hoạt động

  const CSBottomNav({
    super.key,
    required this.selectedIndex,
    this.onChanged,
    this.alertCount = 0,
  });

  @override
  State<CSBottomNav> createState() => _CSBottomNavState();
}

class _CSBottomNavState extends State<CSBottomNav> {
  int? _pressedIndex;

  @override
  Widget build(BuildContext context) {
    const items = [
      (Icons.home_rounded, Icons.home_outlined, 'Trang chủ'),
      (Icons.qr_code_scanner_rounded, Icons.qr_code_scanner_rounded, 'Quét vé'),
      (
        Icons.notifications_rounded,
        Icons.notifications_none_rounded,
        'Cảnh báo',
      ),
      (Icons.settings_rounded, Icons.settings_outlined, 'Cài đặt'),
    ];

    const Color activeBlue = Color(0xFF2464F6);
    final bool isLight = CSAppColors.isLight;
    final Color inactiveSlate = isLight
        ? const Color(0xFF475569)
        : const Color(0xFF94A3B8);

    return SafeArea(
      top: false,
      bottom: true,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(17, 4, 17, 12),
        child: SizedBox(
          height: 70,
          child: Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.center,
            children: [
              // Lớp kính mờ Glassmorphism chuẩn Figma (node 56:290 / 34:2)
              ClipRRect(
                borderRadius: BorderRadius.circular(34),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
                  child: Container(
                    height: 65.5,
                    decoration: BoxDecoration(
                      color: isLight
                          ? Colors.white.withValues(alpha: 0.46)
                          : const Color(0xFF151D2E).withValues(alpha: 0.66),
                      borderRadius: BorderRadius.circular(34),
                      border: Border.all(
                        color: isLight
                            ? Colors.white.withValues(alpha: 0.68)
                            : const Color(0xFF2B3851).withValues(alpha: 0.72),
                        width: 1.1,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(
                            alpha: isLight ? 0.08 : 0.28,
                          ),
                          blurRadius: 36,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              // Hàng 4 mục điều hướng + Quầng sáng xanh mờ (Ô chọn)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                child: Row(
                  children: List.generate(items.length, (index) {
                    final selected = widget.selectedIndex == index;
                    final isPressed = _pressedIndex == index;
                    final item = items[index];
                    final isAlertTab = index == 2;
                    final hasActiveAlert = isAlertTab && widget.alertCount > 0;

                    final Color itemActiveColor = hasActiveAlert
                        ? const Color(0xFFEF4444)
                        : activeBlue;
                    final Color itemInactiveColor = hasActiveAlert
                        ? const Color(0xFFEF4444)
                        : inactiveSlate;

                    // Animation nổi nhẹ mượt mà khi nhấn/chọn
                    final double liftOffset = selected
                        ? -4.0
                        : (isPressed ? -2.0 : 0.0);
                    final double iconScale = selected
                        ? 1.12
                        : (isPressed ? 1.05 : 1.0);

                    return Expanded(
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTapDown: (_) => setState(() => _pressedIndex = index),
                        onTapCancel: () => setState(() => _pressedIndex = null),
                        onTapUp: (_) {
                          setState(() => _pressedIndex = null);
                          HapticFeedback.selectionClick();
                          widget.onChanged?.call(index);
                        },
                        child: Stack(
                          alignment: Alignment.center,
                          clipBehavior: Clip.none,
                          children: [
                            // Quầng sáng xanh mờ "Ô chọn" (82x70, #2464F6 alpha 0.25, blur 30)
                            if (selected)
                              AnimatedContainer(
                                duration: const Duration(milliseconds: 280),
                                width: 78,
                                height: 58,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(30),
                                  gradient: RadialGradient(
                                    colors: [
                                      itemActiveColor.withValues(alpha: 0.26),
                                      itemActiveColor.withValues(alpha: 0.08),
                                      itemActiveColor.withValues(alpha: 0.0),
                                    ],
                                    stops: const [0.0, 0.65, 1.0],
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: itemActiveColor.withValues(
                                        alpha: 0.22,
                                      ),
                                      blurRadius: 24,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                              ),

                            // Icon + Nhãn có hiệu ứng nổi nhẹ lên
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 280),
                              curve: Curves.easeOutBack,
                              transform: Matrix4.translationValues(
                                0,
                                liftOffset,
                                0,
                              ),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  AnimatedScale(
                                    scale: iconScale,
                                    duration: const Duration(milliseconds: 260),
                                    curve: Curves.easeOutBack,
                                    child: Stack(
                                      clipBehavior: Clip.none,
                                      children: [
                                        Icon(
                                          hasActiveAlert
                                              ? Icons
                                                    .notifications_active_rounded
                                              : (selected ? item.$1 : item.$2),
                                          color: selected
                                              ? itemActiveColor
                                              : itemInactiveColor,
                                          size: 22,
                                        ),
                                        if (hasActiveAlert)
                                          Positioned(
                                            right: -8,
                                            top: -5,
                                            child: Container(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                    horizontal: 4.5,
                                                    vertical: 1,
                                                  ),
                                              decoration: BoxDecoration(
                                                color: const Color(0xFFEF4444),
                                                borderRadius:
                                                    BorderRadius.circular(10),
                                                border: Border.all(
                                                  color: Colors.white,
                                                  width: 1.5,
                                                ),
                                              ),
                                              constraints: const BoxConstraints(
                                                minWidth: 15,
                                                minHeight: 15,
                                              ),
                                              child: Text(
                                                widget.alertCount > 99
                                                    ? '99+'
                                                    : '${widget.alertCount}',
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 8.5,
                                                  fontWeight: FontWeight.w800,
                                                ),
                                                textAlign: TextAlign.center,
                                              ),
                                            ),
                                          ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  AnimatedDefaultTextStyle(
                                    duration: const Duration(milliseconds: 220),
                                    style: TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: selected
                                          ? FontWeight.w700
                                          : FontWeight.w500,
                                      color: selected
                                          ? itemActiveColor
                                          : itemInactiveColor,
                                    ),
                                    child: Text(item.$3),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
