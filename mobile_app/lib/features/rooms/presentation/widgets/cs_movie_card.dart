import 'package:flutter/material.dart';
import 'package:mobile_app/core/models/scan_models.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';

class CSMovieCard extends StatelessWidget {
  final CSMockMovie movie;
  final Color statusColor;
  final VoidCallback? onTap;

  const CSMovieCard({
    super.key,
    required this.movie,
    required this.statusColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return CSAppCard(
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 42,
            height: 54,
            decoration: BoxDecoration(
              color: CSAppColors.surfaceStrong,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Icon(
              Icons.movie_outlined,
              color: CSAppColors.muted,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  movie.title,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: CSAppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${movie.time} | ${movie.room}',
                  style: TextStyle(
                    color: CSAppColors.muted,
                    fontSize: 11,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  '● ${movie.status}',
                  style: TextStyle(
                    color: statusColor,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.chevron_right,
            color: CSAppColors.muted,
          ),
        ],
      ),
    );
  }
}
