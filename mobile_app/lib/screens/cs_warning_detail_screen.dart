import 'package:flutter/material.dart';
import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_primary_button.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_seat_map.dart';

class CSWarningDetailScreen extends StatefulWidget {
  final VoidCallback? onResolved;
  const CSWarningDetailScreen({super.key, this.onResolved});

  @override
  State<CSWarningDetailScreen> createState() => _CSWarningDetailScreenState();
}

class _CSWarningDetailScreenState extends State<CSWarningDetailScreen> {
  bool _f5f6Active = true;
  bool _d3d4Active = true;
  
  bool _f5f6Selected = false;
  bool _d3d4Selected = false;

  @override
  Widget build(BuildContext context) {
    final movie = CSMockData.movies.first;
    List<String> ignored = [];
    if (!_f5f6Active) ignored.addAll(['F5', 'F6']);
    if (!_d3d4Active) ignored.addAll(['D3', 'D4']);

    bool hasSelection = _f5f6Selected || _d3d4Selected;

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            const CSScreenHeader(
              title: 'Chi tiết cảnh báo',
              subtitle: 'Rạp 5 • Ghế đang có vấn đề',
              trailingIcon: Icons.settings_outlined,
            ),
            CSAppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(movie.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                  Text('${movie.time} | ${movie.room}', style: const TextStyle(color: CSAppColors.muted, fontSize: 10)),
                ],
              ),
            ),
            const SizedBox(height: 14),
            CSSeatMap(showWarnings: true, ignoredSeats: ignored),
            const SizedBox(height: 16),
            
            if (_f5f6Active)
              GestureDetector(
                onTap: () => setState(() => _f5f6Selected = !_f5f6Selected),
                child: CSWarningStrip(
                  text: 'F5, F6 đang trục trặc',
                  color: CSAppColors.warning,
                  isSelected: _f5f6Selected,
                ),
              ),
            if (_f5f6Active) const SizedBox(height: 8),
            
            if (_d3d4Active)
              GestureDetector(
                onTap: () => setState(() => _d3d4Selected = !_d3d4Selected),
                child: CSWarningStrip(
                  text: 'D3, D4 Đang có người ngồi. Lịch sử check vé chưa ghi nhận check-in vé có chỗ ngồi này',
                  color: CSAppColors.danger,
                  isSelected: _d3d4Selected,
                ),
              ),
            if (_d3d4Active) const SizedBox(height: 12),
            
            // Nút Xử lý
            Opacity(
              opacity: hasSelection ? 1.0 : 0.5,
              child: CSPrimaryButton(
                label: 'Đã xử lý',
                onPressed: hasSelection
                    ? () {
                        setState(() {
                          if (_f5f6Selected) {
                            _f5f6Active = false;
                            _f5f6Selected = false;
                          }
                          if (_d3d4Selected) {
                            _d3d4Active = false;
                            _d3d4Selected = false;
                          }
                        });
                        // Tùy chọn: tự động quay về khi xử lý xong tất cả
                        if (!_f5f6Active && !_d3d4Active) {
                          if (widget.onResolved != null) widget.onResolved!();
                        }
                      }
                    : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class CSWarningStrip extends StatelessWidget {
  final String text;
  final Color color;
  final bool isSelected;

  const CSWarningStrip({super.key, required this.text, required this.color, this.isSelected = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(
        color: isSelected ? color.withValues(alpha: 0.15) : Colors.transparent,
        border: Border.all(color: isSelected ? color : color.withValues(alpha: 0.5), width: isSelected ? 1.5 : 1.0),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.warning_amber, color: color, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(color: color, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
