

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';

import '../widgets/cs_seat_map.dart';

import '../widgets/cs_status_tag.dart';



class CSDamagedSeatScreen extends StatelessWidget {

  final VoidCallback? onAddPhoto;



  const CSDamagedSeatScreen({

    super.key,

    this.onAddPhoto,

  });



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            const Expanded(

              child: SingleChildScrollView(

                padding: EdgeInsets.symmetric(horizontal: 10),

                child: Column(

                  children: [

                    CSScreenHeader(

                      title: 'Sơ đồ ghế - Rạp 5',

                      subtitle: 'Phòng chiếu phim chuẩn Gold Class',

                    ),

                    CSSeatMap(selectionMode: true),

                  ],

                ),

              ),

            ),

            Container(

              padding: const EdgeInsets.all(10),

              decoration: const BoxDecoration(

                color: CSAppColors.surface,

                border: Border(

                  top: BorderSide(color: CSAppColors.border),

                ),

              ),

              child: Column(

                children: [

                  Row(

                    children: [

                      Expanded(

                        child: Text(

                          '${CSMockData.selectedBrokenSeats}',

                          style: TextStyle(fontWeight: FontWeight.w700),

                        ),

                      ),

                      CSStatusTag(

                        text: 'Thay đổi',

                        color: CSAppColors.primary,

                      ),

                    ],

                  ),

                  const SizedBox(height: 10),

                  CSPrimaryButton(

                    label: 'Thêm ảnh ghế hư',

                    icon: Icons.add_a_photo_outlined,

                    onPressed: onAddPhoto,

                  ),

                ],

              ),

            ),

          ],

        ),

      ),

    );

  }

}

