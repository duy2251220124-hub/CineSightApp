

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_screen_header.dart';

import '../widgets/cs_status_tag.dart';



class CSScanHistoryScreen extends StatelessWidget {

  const CSScanHistoryScreen({super.key});



  @override

  Widget build(BuildContext context) {

    final movie = CSMockData.movies.first;



    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            CSScreenHeader(

              title: 'Lịch sử quét vé',

              subtitle: '${movie.title} · ${movie.room}',

            ),

            Padding(

              padding: const EdgeInsets.symmetric(horizontal: 10),

              child: CSAppCard(

                child: Column(

                  crossAxisAlignment: CrossAxisAlignment.start,

                  children: [

                    Text(

                      '${CSMockData.selectedDateLabel} · ${movie.time}',

                      style: const TextStyle(fontWeight: FontWeight.w700),

                    ),

                    Text(

                      'Tổng số vé đã quét: '

                      '${CSMockData.scanSuccess.scanned}/${movie.capacity}',

                      style: const TextStyle(color: CSAppColors.muted),

                    ),

                  ],

                ),

              ),

            ),

            const SizedBox(height: 10),

            const Padding(

              padding: EdgeInsets.symmetric(horizontal: 10),

              child: TextField(

                decoration: InputDecoration(

                  prefixIcon: Icon(Icons.search),

                  hintText: 'Tìm kiếm mã vé, số ghế...',

                  isDense: true,

                ),

              ),

            ),

            const SizedBox(height: 10),

            Expanded(

              child: ListView.builder(

                padding: const EdgeInsets.symmetric(horizontal: 10),

                itemCount: CSMockData.tickets.length,

                itemBuilder: (context, index) {

                  final ticket = CSMockData.tickets[index];



                  return Padding(

                    padding: const EdgeInsets.only(bottom: 8),

                    child: CSAppCard(

                      padding: const EdgeInsets.all(10),

                      child: Row(

                        children: [

                          Expanded(

                            child: Column(

                              crossAxisAlignment: CrossAxisAlignment.start,

                              children: [

                                Text(

                                  ticket.code,

                                  style: const TextStyle(

                                    fontWeight: FontWeight.w700,

                                  ),

                                ),

                                Text(

                                  'Thời gian: ${ticket.scanTime} · '

                                  'NV: ${ticket.employee}',

                                  style: const TextStyle(

                                    color: CSAppColors.muted,

                                    fontSize: 10,

                                  ),

                                ),

                              ],

                            ),

                          ),

                          CSStatusTag(

                            text: 'Ghế ${ticket.seat}',

                            color: CSAppColors.primary,

                          ),

                          const SizedBox(width: 6),

                          CSStatusTag(

                            text: ticket.valid ? 'HỢP LỆ' : 'SAI NGÀY',

                            color: ticket.valid

                                ? CSAppColors.success

                                : CSAppColors.danger,

                          ),

                        ],

                      ),

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

