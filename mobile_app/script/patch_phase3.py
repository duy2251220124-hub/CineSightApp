import os

warning_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
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
"""

warning_detail_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
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
"""

damaged_seat_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/features/rooms/presentation/widgets/cs_seat_map.dart';

class CSDamagedSeatScreen extends StatefulWidget {
  final ValueChanged<List<String>>? onAddPhoto;

  const CSDamagedSeatScreen({super.key, this.onAddPhoto});

  @override
  State<CSDamagedSeatScreen> createState() => _CSDamagedSeatScreenState();
}

class _CSDamagedSeatScreenState extends State<CSDamagedSeatScreen> {
  Set<String> _selectedSeats = {};

  @override
  Widget build(BuildContext context) {
    final seats = _selectedSeats.toList();
    seats.sort();
    final hasSeats = seats.isNotEmpty;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: Column(
                  children: [
                    const CSScreenHeader(
                      title: 'Báo ghế hư',
                      subtitle: 'Chạm vào ghế để chọn / bỏ chọn',
                    ),
                    CSSeatMap(
                      selectionMode: true,
                      selectedSeats: _selectedSeats,
                      onSeatTapped: (seat) {
                        setState(() {
                          if (_selectedSeats.contains(seat)) {
                            _selectedSeats.remove(seat);
                          } else {
                            _selectedSeats.add(seat);
                          }
                        });
                      },
                    ),
                    const SizedBox(height: 12),
                  ],
                ),
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
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          hasSeats
                              ? 'Ghế đã chọn (${seats.length})'
                              : 'Chưa chọn ghế nào',
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      if (hasSeats)
                        TextButton(
                          onPressed: () => setState(() => _selectedSeats.clear()),
                          child: const Text('Bỏ chọn tất cả'),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  if (hasSeats)
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: seats
                          .map(
                            (seat) => InputChip(
                              label: Text(seat),
                              labelStyle: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                              ),
                              backgroundColor: CSAppColors.warning.withValues(alpha: 0.25),
                              side: const BorderSide(
                                color: CSAppColors.warning,
                              ),
                              deleteIconColor: Colors.white,
                              onDeleted: () => setState(() => _selectedSeats.remove(seat)),
                            ),
                          )
                          .toList(),
                    )
                  else
                    const Text(
                      'Chạm vào ghế trên sơ đồ, ghế sẽ chuyển sang màu cam.',
                      style: TextStyle(
                        color: CSAppColors.muted,
                        fontSize: 11,
                      ),
                    ),
                  const SizedBox(height: 10),
                  CSPrimaryButton(
                    label: 'Thêm ảnh ghế hư',
                    icon: Icons.add_a_photo_outlined,
                    onPressed: hasSeats && widget.onAddPhoto != null
                        ? () => widget.onAddPhoto!(seats)
                        : null,
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
"""

add_incident_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSAddIncidentScreen extends StatelessWidget {
  final List<String> reportedSeats;
  final VoidCallback? onSubmit;

  const CSAddIncidentScreen({
    super.key,
    required this.reportedSeats,
    this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Thêm báo cáo sự cố',
              subtitle: 'Chụp ảnh và ghi chú',
            ),
            const Expanded(
              child: Center(
                child: Text('Tính năng chụp ảnh đang phát triển'),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: CSPrimaryButton(
                label: 'Gửi báo cáo',
                onPressed: () {
                  // TODO: Post to backend later
                  onSubmit?.call();
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

handover_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSHandoverScreen extends StatelessWidget {
  const CSHandoverScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const CSScreenHeader(
              title: 'Bàn giao ca',
              subtitle: 'Lịch sử sự cố',
            ),
            const Expanded(
              child: Center(
                child: Text('Chức năng đang phát triển'),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: CSPrimaryButton(
                label: 'Xác nhận bàn giao',
                onPressed: () {
                  Navigator.pop(context);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

incident_detail_screen_content = """import 'package:flutter/material.dart';
import 'package:mobile_app/core/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSIncidentDetailScreen extends StatelessWidget {
  const CSIncidentDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Chi tiết sự cố',
            ),
            Expanded(
              child: Center(
                child: Text('Chức năng đang phát triển'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

with open('lib/features/alerts/presentation/cs_warning_screen.dart', 'w', encoding='utf-8') as f:
    f.write(warning_screen_content)

with open('lib/features/alerts/presentation/cs_warning_detail_screen.dart', 'w', encoding='utf-8') as f:
    f.write(warning_detail_screen_content)

with open('lib/features/alerts/presentation/cs_damaged_seat_screen.dart', 'w', encoding='utf-8') as f:
    f.write(damaged_seat_screen_content)

with open('lib/features/alerts/presentation/cs_add_incident_screen.dart', 'w', encoding='utf-8') as f:
    f.write(add_incident_screen_content)

with open('lib/features/alerts/presentation/cs_handover_screen.dart', 'w', encoding='utf-8') as f:
    f.write(handover_screen_content)

with open('lib/features/alerts/presentation/cs_incident_detail_screen.dart', 'w', encoding='utf-8') as f:
    f.write(incident_detail_screen_content)

# Update HomeShell again to pass alertId to CSWarningDetailScreen
home_screen_path = 'lib/features/home/presentation/home_screen.dart'
with open(home_screen_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
"""                builder: (navCtx) => CSWarningScreen(
                  onWarningSelected: (warning) {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSWarningDetailScreen(
                        onResolved: () => Navigator.pop(ctx),
                      ),
                    ));
                  },""",
"""                builder: (navCtx) => CSWarningScreen(
                  onWarningSelected: (warning) {
                    Navigator.push(navCtx, MaterialPageRoute(
                      builder: (ctx) => CSWarningDetailScreen(
                        alertId: warning['id'] ?? 1,
                        onResolved: () => Navigator.pop(ctx),
                      ),
                    ));
                  },""")

with open(home_screen_path, 'w', encoding='utf-8') as f:
    f.write(content)
