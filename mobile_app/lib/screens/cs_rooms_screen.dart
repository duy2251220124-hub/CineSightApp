

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';



class CSRoomsScreen extends StatefulWidget {

  final ValueChanged<CSMockRoom>? onConfirmed;



  const CSRoomsScreen({

    super.key,

    this.onConfirmed,

  });



  @override

  State<CSRoomsScreen> createState() => _CSRoomsScreenState();

}



class _CSRoomsScreenState extends State<CSRoomsScreen> {

  int _selectedIndex = 4;



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            const CSScreenHeader(

              title: 'Chọn phòng chiếu',

              subtitle: CSMockData.selectedDateLabel,

              trailingIcon: Icons.notifications_none,

            ),

            Expanded(

              child: ListView.builder(

                padding: const EdgeInsets.symmetric(horizontal: 10),

                itemCount: CSMockData.rooms.length,

                itemBuilder: (context, index) {

                  final room = CSMockData.rooms[index];



                  return Padding(

                    padding: const EdgeInsets.only(bottom: 9),

                    child: CSAppCard(

                      borderColor: _selectedIndex == index

                          ? CSAppColors.primary

                          : CSAppColors.border,

                      onTap: () => setState(() => _selectedIndex = index),

                      child: Row(

                        children: [

                          Expanded(

                            child: Column(

                              crossAxisAlignment: CrossAxisAlignment.start,

                              children: [

                                Text(

                                  room.name,

                                  style: const TextStyle(

                                    fontSize: 17,

                                    fontWeight: FontWeight.w700,

                                  ),

                                ),

                                Text(

                                  room.movie,

                                  style: const TextStyle(

                                    color: CSAppColors.muted,

                                    fontSize: 11,

                                  ),

                                ),

                                Text(

                                  room.time,

                                  style: const TextStyle(

                                    color: CSAppColors.muted,

                                    fontSize: 11,

                                  ),

                                ),

                              ],

                            ),

                          ),

                          Text(

                            '● ${room.status}',

                            style: const TextStyle(

                              color: CSAppColors.success,

                              fontSize: 10,

                            ),

                          ),

                        ],

                      ),

                    ),

                  );

                },

              ),

            ),

            Padding(

              padding: const EdgeInsets.all(10),

              child: CSPrimaryButton(

                label: 'Xác nhận phòng chiếu',

                onPressed: () {

                  widget.onConfirmed?.call(

                    CSMockData.rooms[_selectedIndex],

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

