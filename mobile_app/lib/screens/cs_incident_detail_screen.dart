import 'package:flutter/material.dart';
import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_status_tag.dart';

class CSIncidentDetailScreen extends StatelessWidget {
  final CSMockIncident? incident;
  final VoidCallback? onResolved;
  final VoidCallback? onBack;

  const CSIncidentDetailScreen({
    super.key,
    this.incident,
    this.onResolved,
    this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final data = incident ?? CSMockData.incidents.first;
    final color = data.resolved ? CSAppColors.success : CSAppColors.warning;

    return Container(
      height: MediaQuery.of(context).size.height * 0.66,
      decoration: const BoxDecoration(
        color: CSAppColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
      child: SafeArea(
        top: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Grab handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),

            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
            // Header
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        data.title,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Rạp chiếu: ${data.room} • Vị trí: ${data.position}',
                        style: const TextStyle(
                          fontSize: 14,
                          color: CSAppColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                CSStatusTag(
                  text: data.resolved ? 'Đã khắc phục' : 'Chờ xử lý',
                  color: color,
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Detail Block
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: CSAppColors.surfaceStrong,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildDetailRow('Báo cáo bởi', data.reporter),
                  const Divider(color: Colors.white10, height: 24),
                  _buildDetailRow('Thời gian', data.time),
                  const Divider(color: Colors.white10, height: 24),
                  const Text('Mô tả chi tiết', style: TextStyle(color: CSAppColors.muted, fontSize: 13)),
                  const SizedBox(height: 8),
                  Text(
                    data.description,
                    style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.5),
                  ),
                ],
              ),
            ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Buttons
            if (!data.resolved) ...[
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (onResolved != null) onResolved!();
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981), // Green color matching Figma
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 0,
                  ),
                  child: const Text('Đã xử lý', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 12),
            ],
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: () {
                  if (onBack != null) onBack!();
                  Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white24),
                  backgroundColor: CSAppColors.surfaceStrong,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Quay lại danh sách', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: CSAppColors.muted, fontSize: 13)),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
      ],
    );
  }
}
