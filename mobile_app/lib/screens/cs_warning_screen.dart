import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_primary_button.dart';

class CSWarningScreen extends StatelessWidget {
  final ValueChanged<int>? onNavigationChanged;

  final ValueChanged<CSMockWarning>? onWarningSelected;

  final VoidCallback? onIgnoreAll;

  const CSWarningScreen({
    super.key,

    this.onNavigationChanged,

    this.onWarningSelected,

    this.onIgnoreAll,
  });

  Color _color(int severity) {
    return switch (severity) {
      2 => CSAppColors.danger,

      1 => CSAppColors.warning,

      _ => CSAppColors.primary,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Container(
              width: double.infinity,

              padding: const EdgeInsets.all(10),

              decoration: BoxDecoration(
                border: Border.all(color: CSAppColors.danger),
              ),

              child: const Column(
                children: [
                  Text(
                    'PHÁT HIỆN CẢNH BÁO',

                    style: TextStyle(
                      color: CSAppColors.danger,

                      fontWeight: FontWeight.w800,
                    ),
                  ),

                  Text(
                    'Vui lòng kiểm tra lại rạp ngay!',

                    style: TextStyle(color: CSAppColors.danger, fontSize: 11),
                  ),
                ],
              ),
            ),

            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(10),

                itemCount: CSMockData.warnings.length,

                itemBuilder: (context, index) {
                  final warning = CSMockData.warnings[index];

                  final color = _color(warning.severity);

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),

                    child: CSAppCard(
                      onTap: () => onWarningSelected?.call(warning),

                      child: Row(
                        children: [
                          Icon(Icons.warning_amber, color: color, size: 18),

                          const SizedBox(width: 8),

                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,

                              children: [
                                Text(warning.title),

                                const SizedBox(height: 5),

                                Text(
                                  warning.detail,

                                  style: const TextStyle(
                                    color: CSAppColors.muted,

                                    fontSize: 10,
                                  ),
                                ),

                                const SizedBox(height: 7),

                                Text(
                                  'Xem chi tiết',

                                  style: TextStyle(color: color, fontSize: 10),
                                ),
                              ],
                            ),
                          ),

                          Icon(Icons.chevron_right, color: color),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(10),

              child: CSPrimaryButton(
                label: 'Bỏ qua tất cả',

                color: CSAppColors.surface,

                onPressed: onIgnoreAll,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
