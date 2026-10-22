import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';

class CSWarningScreen extends StatefulWidget {
  final ValueChanged<int>? onNavigationChanged;
  final ValueChanged<Map<String, dynamic>>? onWarningSelected;
  final VoidCallback? onIgnoreAll;

  const CSWarningScreen({
    super.key,
    this.onNavigationChanged,
    this.onWarningSelected,
    this.onIgnoreAll,
  });

  @override
  State<CSWarningScreen> createState() => _CSWarningScreenState();
}

class _CSWarningScreenState extends State<CSWarningScreen> {
  List<dynamic> _alerts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    final alerts = await ApiClient.fetchAlerts();
    if (mounted) {
      setState(() {
        _alerts = alerts;
        _isLoading = false;
      });
    }
  }

  Color _color(String type) {
    return type == 'illegal_occupant' ? CSAppColors.danger : CSAppColors.warning;
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
              child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                padding: const EdgeInsets.all(10),
                itemCount: _alerts.length,
                itemBuilder: (context, index) {
                  final warning = _alerts[index];
                  final color = _color(warning['alert_type'] ?? '');
                  final title = warning['alert_type'] == 'illegal_occupant' ? 'Có người lạ/ngồi sai ghế' : 'Ghế rách/trục trặc';

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: CSAppCard(
                      onTap: () {
                        widget.onWarningSelected?.call(warning);
                        _loadAlerts(); // Reload after back
                      },
                      child: Row(
                        children: [
                          Icon(Icons.warning_amber, color: color, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                                const SizedBox(height: 5),
                                Text(
                                  'Ghế bị ảnh hưởng: ${warning['seats'] ?? 'N/A'}',
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
                label: 'Tải lại',
                color: CSAppColors.surface,
                onPressed: _loadAlerts,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
