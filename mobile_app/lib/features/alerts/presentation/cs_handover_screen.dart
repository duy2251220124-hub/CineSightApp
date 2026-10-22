import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/widgets/cs_status_tag.dart';
import 'cs_add_incident_screen.dart';

class CSHandoverScreen extends StatefulWidget {
  const CSHandoverScreen({super.key});

  @override
  State<CSHandoverScreen> createState() => _CSHandoverScreenState();
}

class _CSHandoverScreenState extends State<CSHandoverScreen> {
  List<dynamic> _incidents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadIncidents();
  }

  Future<void> _loadIncidents() async {
    final incidents = await ApiClient.getIncidents();
    if (mounted) {
      setState(() {
        _incidents = incidents;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final pending = _incidents.where((item) => item['status'] == 'open').toList();
    final resolved = _incidents.where((item) => item['status'] == 'resolved').toList();

    return Scaffold(
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(context, MaterialPageRoute(
            builder: (_) => CSAddIncidentScreen(
              reportedSeats: const [],
              onIncidentAdded: () {
                _loadIncidents();
                Navigator.pop(context);
              },
            ),
          ));
        },
        child: const Icon(Icons.add),
      ),
      body: SafeArea(
        child: _isLoading ? const Center(child: CircularProgressIndicator()) : ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            const CSScreenHeader(
              title: 'Sự cố & Bàn giao',
              subtitle: 'Quản lý sự cố kỹ thuật của rạp',
              showBack: true,
            ),
            Text(
              'ĐANG CHỜ XỬ LÝ (${pending.length})',
              style: const TextStyle(
                color: CSAppColors.warning,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 10),
            ...pending.map(
              (incident) => Padding(
                padding: const EdgeInsets.only(bottom: 9),
                child: CSIncidentCard(
                  incident: incident,
                  onResolved: _loadIncidents,
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'ĐÃ KHẮC PHỤC TRONG CA (${resolved.length})',
              style: const TextStyle(
                color: CSAppColors.success,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 10),
            ...resolved.map(
              (incident) => Padding(
                padding: const EdgeInsets.only(bottom: 9),
                child: CSIncidentCard(
                  incident: incident,
                  onResolved: _loadIncidents,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CSIncidentCard extends StatelessWidget {
  final dynamic incident;
  final VoidCallback onResolved;

  const CSIncidentCard({
    super.key,
    required this.incident,
    required this.onResolved,
  });

  @override
  Widget build(BuildContext context) {
    final bool isResolved = incident['status'] == 'resolved';
    final color = isResolved ? CSAppColors.success : CSAppColors.warning;
    final title = incident['title'] ?? 'Sự cố';
    
    // Format date string from ISO
    String dateStr = incident['created_at'] ?? '';
    if (dateStr.isNotEmpty) {
      try {
        final dt = DateTime.parse(dateStr).toLocal();
        dateStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day}/${dt.month}/${dt.year}';
      } catch (_) {}
    }

    return CSAppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
              CSStatusTag(
                text: isResolved ? 'Đã khắc phục' : 'Chờ xử lý',
                color: color,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Phòng: ${incident['room_id'] ?? 'N/A'} - Suất: ${incident['show_id'] ?? 'N/A'}',
            style: const TextStyle(
              color: CSAppColors.muted,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Báo cáo bởi: ${incident['reporter_name'] ?? 'Ẩn danh'} (${incident['shift_label'] ?? 'Ca'})',
            style: const TextStyle(
              color: CSAppColors.muted,
              fontSize: 11,
            ),
          ),
          if (dateStr.isNotEmpty)
            Text(
              'Lúc: $dateStr',
              style: const TextStyle(
                color: CSAppColors.muted,
                fontSize: 11,
              ),
            ),
          if (!isResolved) ...[
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () async {
                    final res = await ApiClient.resolveIncident(incident['id']);
                    if (res['success'] == true) {
                      onResolved();
                    } else {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(res['error'] ?? 'Lỗi')),
                        );
                      }
                    }
                  },
                  child: const Text('Đánh dấu đã xử lý'),
                ),
              ],
            ),
          ]
        ],
      ),
    );
  }
}
