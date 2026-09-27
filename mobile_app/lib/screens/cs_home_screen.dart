import 'package:flutter/material.dart';

import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_movie_card.dart';
import '../widgets/cs_status_tag.dart';

class CSHomeScreen extends StatelessWidget {
  final VoidCallback? onNotifications;
  final VoidCallback? onShowtimes;
  final VoidCallback? onRooms;
  final VoidCallback? onHandover;

  const CSHomeScreen({
    super.key,
    this.onNotifications,
    this.onShowtimes,
    this.onRooms,
    this.onHandover,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(14),
          children: [
            Row(
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        CSMockData.employeeName,
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                      Text(
                        '${CSMockData.employeeRole} · ${CSMockData.employeeId}',
                        style: TextStyle(
                          color: CSAppColors.muted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: onNotifications,
                  icon: const Icon(Icons.notifications_none),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const CSAppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          CSMockData.cinemaName,
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      CSStatusTag(
                        text: '● ON SHIFT',
                        color: CSAppColors.success,
                      ),
                    ],
                  ),
                  SizedBox(height: 10),
                  Text('Ca làm việc: ${CSMockData.shiftTime}'),
                  SizedBox(height: 5),
                  Text('Rạp đang hoạt động: ${CSMockData.activeRooms}'),
                ],
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                CSHomeAction(
                  icon: Icons.calendar_month_outlined,
                  label: 'Suất chiếu',
                  onTap: onShowtimes,
                ),
                CSHomeAction(
                  icon: Icons.videocam_outlined,
                  label: 'Phòng chiếu',
                  onTap: onRooms,
                ),
                CSHomeAction(
                  icon: Icons.handyman_outlined,
                  label: 'Sự cố & BG',
                  onTap: onHandover,
                ),
              ],
            ),
            const SizedBox(height: 18),
            const Text(
              'Các suất gần nhất',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            ...List.generate(CSMockData.movies.length, (index) {
              final colors = [
                CSAppColors.success,
                CSAppColors.warning,
                CSAppColors.danger,
              ];

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: CSMovieCard(
                  movie: CSMockData.movies[index],
                  statusColor: colors[index],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class CSHomeAction extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const CSHomeAction({
    super.key,
    required this.icon,
    required this.label,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: CSAppCard(
          onTap: onTap,
          padding: const EdgeInsets.symmetric(vertical: 14),
          child: Column(
            children: [
              Icon(icon, color: CSAppColors.primary, size: 30),
              const SizedBox(height: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
