

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';

import '../widgets/cs_seat_map.dart';



class CSWarningDetailScreen extends StatelessWidget {

  final VoidCallback? onResolved;



  const CSWarningDetailScreen({

    super.key,

    this.onResolved,

  });



  @override

  Widget build(BuildContext context) {

    final movie = CSMockData.movies.first;



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

                ],

              ),

            ),

            const SizedBox(height: 14),

            const CSSeatMap(showWarnings: true),

            const SizedBox(height: 16),

            const CSWarningStrip(

              text: 'F5, F6 đang trục trặc',

              color: CSAppColors.warning,

            ),

            const SizedBox(height: 8),

            const CSWarningStrip(

              text:

                  'D3, D4 đang có người ngồi nhưng chưa ghi nhận check-in.',

              color: CSAppColors.danger,

            ),

            const SizedBox(height: 12),

            CSPrimaryButton(

              label: 'Đã xử lý',

              onPressed: onResolved,

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



  const CSWarningStrip({

    super.key,

    required this.text,

    required this.color,

  });



  @override

  Widget build(BuildContext context) {

    return Container(

      padding: const EdgeInsets.all(11),

      decoration: BoxDecoration(

        border: Border.all(color: color),

        borderRadius: BorderRadius.circular(8),

      ),

      child: Row(

        children: [

          Icon(Icons.warning_amber, color: color),

          const SizedBox(width: 8),

          Expanded(

            child: Text(

              text,

              style: TextStyle(color: color, fontSize: 11),

            ),

          ),

        ],

      ),

    );

  }

}

