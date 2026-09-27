

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';

import '../widgets/cs_status_tag.dart';



class CSOfflineScreen extends StatelessWidget {

  final VoidCallback? onRetry;



  const CSOfflineScreen({

    super.key,

    this.onRetry,

  });



  @override

  Widget build(BuildContext context) {

    final movie = CSMockData.movies.first;



    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            const CSScreenHeader(

              title: 'Đồng bộ offline',

              subtitle: 'Quản lý dữ liệu khi mất mạng',

              trailingIcon: Icons.notifications_none,

            ),

            Expanded(

              child: ListView(

                padding: const EdgeInsets.all(10),

                children: [

                  const CSOfflineStatusCard(

                    icon: Icons.cloud_off,

                    title: 'Chờ đồng bộ: 3 vé',

                    detail: 'Dữ liệu soát vé lưu tạm thời trên máy',

                    color: CSAppColors.warning,

                    status: 'Đợi',

                  ),

                  const SizedBox(height: 10),

                  const CSOfflineStatusCard(

                    icon: Icons.sync,

                    title: 'Đã đồng bộ',

                    detail: '117 vé đã lưu trữ đám mây',

                    color: CSAppColors.success,

                    status: 'OK',

                  ),

                  const SizedBox(height: 10),

                  CSAppCard(

                    child: Column(

                      crossAxisAlignment: CrossAxisAlignment.start,

                      children: [

                        Text(

                          movie.title,

                          style: const TextStyle(

                            fontWeight: FontWeight.w700,

                          ),

                        ),

                        Text(

                          '${movie.time} | ${movie.room}',

                          style: const TextStyle(

                            color: CSAppColors.muted,

                            fontSize: 11,

                          ),

                        ),

                        const SizedBox(height: 20),

                        const Row(

                          children: [

                            Expanded(

                              child: Text(

                                'Trạng thái mạng',

                                style: TextStyle(

                                  color: CSAppColors.muted,

                                  fontSize: 11,

                                ),

                              ),

                            ),

                            Text(

                              '● Mất kết nối',

                              style: TextStyle(

                                color: CSAppColors.danger,

                                fontSize: 11,

                              ),

                            ),

                          ],

                        ),

                      ],

                    ),

                  ),

                ],

              ),

            ),

            Padding(

              padding: const EdgeInsets.all(10),

              child: CSPrimaryButton(

                label: 'Thử đồng bộ lại',

                icon: Icons.sync,

                onPressed: onRetry,

              ),

            ),

          ],

        ),

      ),

    );

  }

}



class CSOfflineStatusCard extends StatelessWidget {

  final IconData icon;

  final String title;

  final String detail;

  final Color color;

  final String status;



  const CSOfflineStatusCard({

    super.key,

    required this.icon,

    required this.title,

    required this.detail,

    required this.color,

    required this.status,

  });



  @override

  Widget build(BuildContext context) {

    return CSAppCard(

      child: Row(

        children: [

          CircleAvatar(

            backgroundColor: color.withValues(alpha: .14),

            child: Icon(icon, color: color),

          ),

          const SizedBox(width: 12),

          Expanded(

            child: Column(

              crossAxisAlignment: CrossAxisAlignment.start,

              children: [

                Text(

                  title,

                  style: const TextStyle(fontWeight: FontWeight.w700),

                ),

                Text(

                  detail,

                  style: const TextStyle(

                    color: CSAppColors.muted,

                    fontSize: 10,

                  ),

                ),

              ],

            ),

          ),

          CSStatusTag(text: status, color: color),

        ],

      ),

    );

  }

}
