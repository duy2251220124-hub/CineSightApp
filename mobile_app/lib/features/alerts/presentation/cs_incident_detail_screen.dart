import 'package:flutter/material.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

class CSIncidentDetailScreen extends StatelessWidget {
  const CSIncidentDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            CSScreenHeader(
              title: 'Chi tiết sự cố',
            ),
            Expanded(
              child: Center(
                child: Text('Chức năng đang phát triển'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
