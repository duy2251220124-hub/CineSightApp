import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:mobile_app/main.dart';

void main() {
  setUpAll(() async {
    final tempDir = Directory.systemTemp.createTempSync('hive_test_widget');
    Hive.init(tempDir.path);
    await Hive.openBox<String>('scanned_tickets_box');
    await Hive.openBox<String>('scan_history_box');
  });

  testWidgets('App initializes smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MyApp), findsOneWidget);
  });
}
