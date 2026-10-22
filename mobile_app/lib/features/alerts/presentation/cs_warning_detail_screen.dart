import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSWarningDetailScreen extends StatelessWidget {
  final VoidCallback? onResolved;
  final int alertId;

  const CSWarningDetailScreen({super.key, this.onResolved, this.alertId = 1}); // default to 1 if not passed for simplicity

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Chi tiết cảnh báo',
              subtitle: 'Đang xem',
            ),
            const Expanded(
              child: Center(
                child: Text('Ảnh camera sẽ hiển thị ở đây (Kết nối sau)'),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                color: CSAppColors.surface,
                border: Border(top: BorderSide(color: CSAppColors.border)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Sự cố AI phát hiện', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  const SizedBox(height: 10),
                  CSPrimaryButton(
                    label: 'Xác nhận đã giải quyết',
                    icon: Icons.check_circle_outline,
                    onPressed: () async {
                      await ApiClient.resolveAlert(alertId);
                      onResolved?.call();
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
