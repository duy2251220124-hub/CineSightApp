

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';

import '../widgets/cs_status_tag.dart';



class CSIncidentDetailScreen extends StatelessWidget {

  final CSMockIncident? incident;

  final VoidCallback? onResolved;

  final VoidCallback? onBack;



  const CSIncidentDetailScreen({

    super.key,

    this.incident,

    this.onResolved,

    this.onBack,

  });



  @override

  Widget build(BuildContext context) {
    final incident = this.incident ?? CSMockData.incidents.first;

    return Scaffold(

      body: SafeArea(

        child: Column(

          children: [

            CSScreenHeader(

              title: 'Sự cố & Bàn giao',

              subtitle: 'Quản lý sự cố kỹ thuật của rạp',

              onBack: onBack,

            ),

            Expanded(

              child: ListView(

                padding: const EdgeInsets.all(10),

                children: [

                  Row(

                    children: [

                      Expanded(

                        child: Text(

                          incident.title,

                          style: const TextStyle(

                            fontSize: 17,

                            fontWeight: FontWeight.w700,

                          ),

                        ),

                      ),

                      CSStatusTag(

                        text: incident.resolved

                            ? 'Đã xử lý'

                            : 'Chờ xử lý',

                        color: incident.resolved

                            ? CSAppColors.success

                            : CSAppColors.warning,

                      ),

                    ],

                  ),

                  const SizedBox(height: 7),

                  Text(

                    'Rạp chiếu: ${incident.room} • '

                    'Vị trí: ${incident.position}',

                    style: const TextStyle(

                      color: CSAppColors.muted,

                      fontSize: 11,

                    ),

                  ),

                  const SizedBox(height: 120),

                  CSAppCard(

                    color: CSAppColors.background,

                    child: Column(

                      crossAxisAlignment: CrossAxisAlignment.start,

                      children: [

                        CSIncidentInfoRow(

                          label: 'Báo cáo bởi',

                          value: incident.reporter,

                        ),

                        const Divider(),

                        CSIncidentInfoRow(

                          label: 'Thời gian',

                          value: incident.time,

                        ),

                        const Divider(),

                        const Text(

                          'Mô tả chi tiết',

                          style: TextStyle(color: CSAppColors.muted),

                        ),

                        const SizedBox(height: 8),

                        Text(incident.description),

                      ],

                    ),

                  ),

                ],

              ),

            ),

            Padding(

              padding: const EdgeInsets.all(10),

              child: Column(

                children: [

                  CSPrimaryButton(

                    label: 'Đã xử lý',

                    color: CSAppColors.success,

                    onPressed: onResolved,

                  ),

                  const SizedBox(height: 8),

                  SizedBox(

                    width: double.infinity,

                    child: OutlinedButton(

                      onPressed: onBack,

                      child: const Text('Quay lại danh sách'),

                    ),

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



class CSIncidentInfoRow extends StatelessWidget {

  final String label;

  final String value;



  const CSIncidentInfoRow({

    super.key,

    required this.label,

    required this.value,

  });



  @override

  Widget build(BuildContext context) {

    return Row(

      children: [

        Expanded(

          child: Text(

            label,

            style: const TextStyle(color: CSAppColors.muted),

          ),

        ),

        Text(

          value,

          style: const TextStyle(fontWeight: FontWeight.w700),

        ),

      ],

    );

  }

}

