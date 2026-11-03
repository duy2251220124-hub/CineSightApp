import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';

class CSBottomNav extends StatelessWidget {
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
  Widget build(BuildContext context) {
    const items = [
      (Icons.home_outlined, 'Trang chủ'),
      (Icons.confirmation_number_outlined, 'Quét vé'),
      (Icons.notifications_none, 'Cảnh báo'),
      (Icons.settings_outlined, 'Cài đặt'),
    ];

    return Container(
      decoration: const BoxDecoration(
        color: CSAppColors.surface,
        border: Border(
          top: BorderSide(color: CSAppColors.border),
        ),
      ),
      child: SafeArea(
        top: false,
        bottom: true,
        child: SizedBox(
          height: 60,
          child: Row(
            children: List.generate(items.length, (index) {
              final selected = selectedIndex == index;
              final item = items[index];
              final isAlertTab = index == 2;

              return Expanded(
                child: InkWell(
                  onTap: () => onChanged?.call(index),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Stack(
                        clipBehavior: Clip.none,
                        children: [
                          Icon(
                            isAlertTab && alertCount > 0
                                ? Icons.notifications_active
                                : item.$1,
                            color: isAlertTab && alertCount > 0
                                ? CSAppColors.danger
                                : (selected ? CSAppColors.primary : CSAppColors.muted),
                            size: 24,
                          ),
                          if (isAlertTab && alertCount > 0)
                            Positioned(
                              right: -8,
                              top: -4,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                                decoration: BoxDecoration(
                                  color: CSAppColors.danger,
                                  borderRadius: BorderRadius.circular(10),
                                  boxShadow: const [
                                    BoxShadow(
                                      color: Colors.black45,
                                      blurRadius: 4,
                                      offset: Offset(0, 1),
                                    ),
                                  ],
                                ),
                                constraints: const BoxConstraints(minWidth: 16, minHeight: 16),
                                child: Text(
                                  alertCount > 99 ? '99+' : '$alertCount',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item.$2,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                          color: isAlertTab && alertCount > 0
                              ? CSAppColors.danger
                              : (selected ? CSAppColors.primary : CSAppColors.muted),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}
