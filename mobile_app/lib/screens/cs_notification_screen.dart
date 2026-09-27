

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_bottom_nav.dart';

import '../widgets/cs_status_tag.dart';



class CSNotificationScreen extends StatelessWidget {

  final ValueChanged<int>? onNavigationChanged;

  final VoidCallback? onViewAll;



  const CSNotificationScreen({

    super.key,

    this.onNavigationChanged,

    this.onViewAll,

  });



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      bottomNavigationBar: CSBottomNav(

        selectedIndex: 0,

        onChanged: onNavigationChanged,

      ),

      body: SafeArea(

        child: Stack(

          children: [

            const Positioned(

              top: 10,

              left: 0,

              right: 0,

              child: Column(

                children: [

                  Text(

                    CSMockData.employeeName,

                    style: TextStyle(fontWeight: FontWeight.w700),

                  ),

                  Text(

                    '${CSMockData.employeeRole} · ${CSMockData.employeeId}',

                    style: TextStyle(

                      color: CSAppColors.muted,

                      fontSize: 10,

                    ),

                  ),

                ],

              ),

            ),

            Positioned(

              top: 54,

              left: 20,

              right: 20,

              child: CSAppCard(

                borderColor: CSAppColors.primary,

                child: Column(

                  children: [

                    Row(

                      children: [

                        const Expanded(

                          child: Row(

                            children: [

                              Text(

                                'Thông báo mới',

                                style: TextStyle(

                                  fontWeight: FontWeight.w700,

                                ),

                              ),

                              SizedBox(width: 7),

                              CSStatusTag(

                                text: '3',

                                color: CSAppColors.danger,

                              ),

                            ],

                          ),

                        ),

                        TextButton(

                          onPressed: onViewAll,

                          child: const Text('Xem tất cả'),

                        ),

                      ],

                    ),

                    ...CSMockData.notifications.map(

                      (notification) => Column(

                        children: [

                          const Divider(),

                          CSNotificationItemView(

                            notification: notification,

                          ),

                        ],

                      ),

                    ),

                  ],

                ),

              ),

            ),

          ],

        ),

      ),

    );

  }

}



class CSNotificationItemView extends StatelessWidget {

  final CSMockNotification notification;



  const CSNotificationItemView({

    super.key,

    required this.notification,

  });



  @override

  Widget build(BuildContext context) {

    return Padding(

      padding: const EdgeInsets.symmetric(vertical: 7),

      child: Column(

        crossAxisAlignment: CrossAxisAlignment.start,

        children: [

          Text(

            notification.title,

            style: const TextStyle(fontWeight: FontWeight.w700),

          ),

          const SizedBox(height: 6),

          Text(

            notification.detail,

            style: const TextStyle(

              color: CSAppColors.muted,

              fontSize: 11,

            ),

          ),

          const SizedBox(height: 5),

          Text(

            notification.time,

            style: const TextStyle(

              color: CSAppColors.muted,

              fontSize: 9,

            ),

          ),

        ],

      ),

    );

  }

}

