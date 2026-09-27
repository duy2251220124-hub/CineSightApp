

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_movie_card.dart';

import '../widgets/cs_screen_header.dart';



class CSShowtimesScreen extends StatelessWidget {

  final ValueChanged<CSMockMovie>? onMovieSelected;



  const CSShowtimesScreen({

    super.key,

    this.onMovieSelected,

  });



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            const CSScreenHeader(

              title: 'Chọn suất chiếu',

              subtitle: CSMockData.selectedDateLabel,

              trailingIcon: Icons.notifications_none,

            ),

            const Padding(

              padding: EdgeInsets.symmetric(horizontal: 10),

              child: TextField(

                decoration: InputDecoration(

                  prefixIcon: Icon(Icons.search),

                  hintText: 'Tên phim',

                  isDense: true,

                ),

              ),

            ),

            const SizedBox(height: 12),

            Expanded(

              child: ListView.builder(

                padding: const EdgeInsets.symmetric(horizontal: 10),

                itemCount: CSMockData.movies.length,

                itemBuilder: (context, index) {

                  final movie = CSMockData.movies[index];

                  final colors = [

                    CSAppColors.success,

                    CSAppColors.warning,

                    CSAppColors.danger,

                  ];



                  return Padding(

                    padding: const EdgeInsets.only(bottom: 10),

                    child: CSMovieCard(

                      movie: movie,

                      statusColor: colors[index],

                      onTap: () => onMovieSelected?.call(movie),

                    ),

                  );

                },

              ),

            ),

          ],

        ),

      ),

    );

  }

}

