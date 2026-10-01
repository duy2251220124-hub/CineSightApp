

import 'package:flutter/material.dart';
import '../mock/mock_data.dart';
import '../theme/app_theme.dart';
import '../widgets/cs_app_card.dart';
import '../widgets/cs_screen_header.dart';
import '../widgets/cs_status_tag.dart';
import 'cs_incident_detail_screen.dart';
import 'cs_add_incident_screen.dart';
class CSHandoverScreen extends StatelessWidget {

  final ValueChanged<int>? onNavigationChanged;

  final ValueChanged<CSMockIncident>? onIncidentSelected;

  final VoidCallback? onAddIncident;



  const CSHandoverScreen({

    super.key,

    this.onNavigationChanged,

    this.onIncidentSelected,

    this.onAddIncident,

  });



  @override

  Widget build(BuildContext context) {

    final pending =

        CSMockData.incidents.where((item) => !item.resolved).toList();

    final resolved =

        CSMockData.incidents.where((item) => item.resolved).toList();



    return Scaffold(

      

      floatingActionButton: FloatingActionButton(

        onPressed: onAddIncident ?? () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CSAddIncidentScreen())),

        child: const Icon(Icons.add),

      ),

      body: SafeArea(

        child: ListView(

          padding: const EdgeInsets.symmetric(horizontal: 10),

          children: [

            const CSScreenHeader(

              title: 'Sự cố & Bàn giao',

              subtitle: 'Quản lý sự cố kỹ thuật của rạp',

              showBack: false,

            ),

            Text(

              'ĐANG CHỜ XỬ LÝ (${pending.length})',

              style: const TextStyle(

                color: CSAppColors.warning,

                fontWeight: FontWeight.w700,

              ),

            ),

            const SizedBox(height: 10),

            ...pending.map(

              (incident) => Padding(

                padding: const EdgeInsets.only(bottom: 9),

                child: CSIncidentCard(

                  incident: incident,

                  onTap: () => onIncidentSelected != null ? onIncidentSelected!(incident) : showDialog(context: context, builder: (_) => AlertDialog(contentPadding: EdgeInsets.zero, backgroundColor: Colors.transparent, content: CSIncidentDetailScreen(incident: incident))),

                ),

              ),

            ),

            const SizedBox(height: 12),

            Text(

              'ĐÃ KHẮC PHỤC TRONG CA (${resolved.length})',

              style: const TextStyle(

                color: CSAppColors.success,

                fontWeight: FontWeight.w700,

              ),

            ),

            const SizedBox(height: 10),

            ...resolved.map(

              (incident) => CSIncidentCard(incident: incident),

            ),

          ],

        ),

      ),

    );

  }

}



class CSIncidentCard extends StatelessWidget {

  final CSMockIncident incident;

  final VoidCallback? onTap;



  const CSIncidentCard({

    super.key,

    required this.incident,

    this.onTap,

  });



  @override

  Widget build(BuildContext context) {

    final color = incident.resolved

        ? CSAppColors.success

        : CSAppColors.warning;



    return CSAppCard(

      onTap: onTap,

      child: Column(

        crossAxisAlignment: CrossAxisAlignment.start,

        children: [

          Row(

            children: [

              Expanded(

                child: Text(

                  incident.title,

                  style: const TextStyle(fontWeight: FontWeight.w700),

                ),

              ),

              CSStatusTag(

                text: incident.resolved ? 'Đã khắc phục' : 'Chờ xử lý',

                color: color,

              ),

            ],

          ),

          const SizedBox(height: 8),

          Text(

            'Báo cáo bởi: ${incident.reporter}',

            style: const TextStyle(

              color: CSAppColors.muted,

              fontSize: 11,

            ),

          ),

          const SizedBox(height: 8),

          Text(

            incident.description,

            style: const TextStyle(

              color: CSAppColors.muted,

              fontSize: 11,

            ),

          ),

        ],

      ),

    );

  }

}



