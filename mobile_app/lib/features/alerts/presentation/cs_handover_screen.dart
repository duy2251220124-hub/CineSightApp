import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
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
            builder: (addCtx) => CSAddIncidentScreen(
              reportedSeats: const [],
              onIncidentAdded: () {
                _loadIncidents();
                Navigator.pop(addCtx);
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ĐÃ KHẮC PHỤC TRONG CA (${resolved.length})',
                        style: const TextStyle(
                          color: CSAppColors.success,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        'Tự động làm sạch sau 1 tiếng kể từ lúc giải quyết',
                        style: TextStyle(color: CSAppColors.muted, fontSize: 10),
                      ),
                    ],
                  ),
                ),
                if (resolved.isNotEmpty)
                  TextButton.icon(
                    style: TextButton.styleFrom(
                      foregroundColor: CSAppColors.danger,
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    ),
                    onPressed: () async {
                      final confirmed = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          backgroundColor: CSAppColors.surfaceStrong,
                          title: const Text('Dọn sạch sự cố đã xử lý?', style: TextStyle(fontSize: 15)),
                          content: const Text(
                            'Toàn bộ các sự cố đã khắc phục sẽ được xóa ngay lập tức khỏi hệ thống.',
                            style: TextStyle(fontSize: 13, color: CSAppColors.muted),
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(ctx, false),
                              child: const Text('Hủy'),
                            ),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: CSAppColors.danger),
                              onPressed: () => Navigator.pop(ctx, true),
                              child: const Text('Xóa tất cả', style: TextStyle(color: Colors.white)),
                            ),
                          ],
                        ),
                      );
                      if (confirmed == true) {
                        await ApiClient.clearResolvedIncidents();
                        _loadIncidents();
                      }
                    },
                    icon: const Icon(Icons.delete_sweep_outlined, size: 16),
                    label: const Text('Dọn sạch', style: TextStyle(fontSize: 11)),
                  ),
              ],
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

    String resolvedStr = incident['resolved_at'] ?? '';
    if (resolvedStr.isNotEmpty) {
      try {
        final dt = DateTime.parse(resolvedStr).toLocal();
        resolvedStr = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')} - ${dt.day}/${dt.month}/${dt.year}';
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
            '${formatRoomName(incident['room_id']?.toString())} - Suất: ${incident['show_id'] ?? 'N/A'}',
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
          if (incident['description'] != null && incident['description'].toString().trim().isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              incident['description'].toString(),
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
          if (incident['image_path'] != null && incident['image_path'].toString().trim().isNotEmpty) ...[
            const SizedBox(height: 10),
            Builder(
              builder: (ctx) {
                final rawPath = incident['image_path'].toString().trim();
                final imgUrl = rawPath.startsWith('http')
                    ? rawPath
                    : '${ApiClient.baseUrl.replaceAll(RegExp(r'/+$'), '')}$rawPath';
                return ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: InkWell(
                    onTap: () {
                      showDialog(
                        context: ctx,
                        builder: (_) => Dialog(
                          backgroundColor: Colors.transparent,
                          insetPadding: const EdgeInsets.all(12),
                          child: Stack(
                            alignment: Alignment.topRight,
                            children: [
                              InteractiveViewer(
                                child: Image.network(
                                  imgUrl,
                                  headers: const {'ngrok-skip-browser-warning': 'true'},
                                  fit: BoxFit.contain,
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, color: Colors.white, size: 28),
                                onPressed: () => Navigator.pop(ctx),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                    child: Stack(
                      alignment: Alignment.bottomRight,
                      children: [
                        Image.network(
                          imgUrl,
                          height: 140,
                          width: double.infinity,
                          fit: BoxFit.cover,
                          headers: const {'ngrok-skip-browser-warning': 'true'},
                          errorBuilder: (context, error, stackTrace) => Container(
                            height: 80,
                            color: CSAppColors.surfaceStrong,
                            alignment: Alignment.center,
                            child: const Text('Không tải được ảnh hiện trường', style: TextStyle(color: CSAppColors.muted, fontSize: 11)),
                          ),
                        ),
                        Container(
                          margin: const EdgeInsets.all(6),
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                          decoration: BoxDecoration(
                            color: Colors.black.withValues(alpha: 0.75),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.zoom_in, size: 14, color: Colors.white),
                              SizedBox(width: 4),
                              Text('Xem ảnh', style: TextStyle(color: Colors.white, fontSize: 10)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
          if (isResolved && resolvedStr.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'Khắc phục lúc: $resolvedStr (Tự xóa sau 1h)',
                style: const TextStyle(
                  color: CSAppColors.success,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              if (!isResolved) ...[
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
                const SizedBox(width: 8),
              ],
              TextButton.icon(
                style: TextButton.styleFrom(
                  foregroundColor: isResolved ? CSAppColors.danger : CSAppColors.muted,
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                ),
                onPressed: () async {
                  final confirmed = await showDialog<bool>(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      backgroundColor: CSAppColors.surfaceStrong,
                      title: const Text('Xóa sự cố này?', style: TextStyle(fontSize: 15)),
                      content: Text(
                        'Bạn có chắc chắn muốn xóa sự cố "${incident['title'] ?? 'N/A'}" ngay lập tức?',
                        style: const TextStyle(fontSize: 13, color: CSAppColors.muted),
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Hủy'),
                        ),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(backgroundColor: CSAppColors.danger),
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Xóa ngay', style: TextStyle(color: Colors.white)),
                        ),
                      ],
                    ),
                  );
                  if (confirmed == true) {
                    final res = await ApiClient.deleteIncident(incident['id']);
                    if (res['success'] == true) {
                      onResolved();
                    } else {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(res['error'] ?? 'Không thể xóa sự cố')),
                        );
                      }
                    }
                  }
                },
                icon: const Icon(Icons.delete_outline, size: 16),
                label: Text(
                  isResolved ? 'Xóa sự cố ngay' : 'Xóa',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          )
        ],
      ),
    );
  }
}
