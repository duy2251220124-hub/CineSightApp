import 'package:flutter/material.dart';

import '../mock/mock_data.dart';
import '../mock/seat_report_store.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_primary_button.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_seat_map.dart';

class CSSeatMapScreen extends StatelessWidget {
  final VoidCallback? onReportDamagedSeat;

  const CSSeatMapScreen({super.key, this.onReportDamagedSeat});

  @override
  Widget build(BuildContext context) {
    final movie = CSMockData.movies.first;
    final percentage = movie.sold * 100 ~/ movie.capacity;

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          children: [
            const CSScreenHeader(
              title: 'Sơ đồ ghế - Rạp 5',
              subtitle: 'Phòng chiếu phim chuẩn Gold Class',
              trailingIcon: Icons.settings_outlined,
            ),
            CSAppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    movie.title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  Text(
                    '${movie.time} | ${movie.room}',
                    style: const TextStyle(
                      color: CSAppColors.muted,
                      fontSize: 10,
                    ),
                  ),
                  Row(
                    children: [
                      Text(
                        'Đã bán: ${movie.sold}/${movie.capacity}',
                        style: const TextStyle(
                          color: CSAppColors.muted,
                          fontSize: 10,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '$percentage%',
                        style: const TextStyle(
                          color: CSAppColors.primary,
                          fontSize: 10,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Chạm vào ghế trên sơ đồ để chọn ghế hư',
              textAlign: TextAlign.center,
              style: TextStyle(color: CSAppColors.muted, fontSize: 11),
            ),
            const SizedBox(height: 10),
            const CSSeatMap(selectionMode: true),
            const SizedBox(height: 22),
            ValueListenableBuilder<Set<String>>(
              valueListenable: SeatReportStore.selected,
              builder: (context, selected, _) {
                final count = selected.length;
                return CSPrimaryButton(
                  label: count == 0 ? 'Báo ghế hư' : 'Báo ghế hư ($count ghế)',
                  icon: Icons.report_problem_outlined,
                  onPressed: onReportDamagedSeat,
                );
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
