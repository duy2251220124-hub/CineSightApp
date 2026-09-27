import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class CSScreenHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final bool showBack;
  final IconData? trailingIcon;
  final VoidCallback? onBack;
  final VoidCallback? onTrailing;

  const CSScreenHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.showBack = true,
    this.trailingIcon,
    this.onBack,
    this.onTrailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 14),
      child: Row(
        children: [
          if (showBack)
            IconButton(
              onPressed: onBack ?? () => Navigator.maybePop(context),
              icon: const Icon(Icons.chevron_left),
              style: IconButton.styleFrom(backgroundColor: CSAppColors.surface),
            ),
          if (showBack) const SizedBox(width: 4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: const TextStyle(
                      color: CSAppColors.muted,
                      fontSize: 11,
                    ),
                  ),
              ],
            ),
          ),
          if (trailingIcon != null)
            IconButton(
              onPressed: onTrailing,
              icon: Icon(trailingIcon, size: 19),
              style: IconButton.styleFrom(backgroundColor: CSAppColors.surface),
            ),
        ],
      ),
    );
  }
}
