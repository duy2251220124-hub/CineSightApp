

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import 'cs_app_card.dart';



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

              color: Colors.white,

              borderRadius: BorderRadius.circular(4),

            ),

          ),

          const SizedBox(width: 12),

          Expanded(

            child: Column(

              crossAxisAlignment: CrossAxisAlignment.start,

              children: [

                Text(

                  movie.title,

                  style: const TextStyle(fontWeight: FontWeight.w700),

                ),

                const SizedBox(height: 4),

                Text(

                  '${movie.time} | ${movie.room}',

                  style: const TextStyle(

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

          const Icon(

            Icons.chevron_right,

            color: CSAppColors.muted,

          ),

        ],

      ),

    );

  }

}






