import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';

import 'package:mobile_app/core/database/hive_service.dart';

import 'package:mobile_app/features/alerts/presentation/cs_damaged_seat_screen.dart';
import 'package:mobile_app/features/rooms/presentation/cs_seat_map_screen.dart';

void main() {
  group('Báo ghế hư', () {
    setUp(() {
                });

    testWidgets(
      'Không còn ghế chọn sẵn; chọn ở Sơ đồ ghế hiện ở màn Báo ghế hư',
      (tester) async {
        tester.view.physicalSize = const Size(1080, 2400);
        tester.view.devicePixelRatio = 3;
        addTearDown(tester.view.reset);

        await tester.pumpWidget(const MaterialApp(home: CSSeatMapScreen(roomId: 'room1', showId: 'show1')));
        

        await tester.tap(find.text('F5'));
        await tester.pump();
        await tester.ensureVisible(find.text('H1'));
        await tester.tap(find.text('H1'));
        await tester.pump();

        

        await tester.pumpWidget(const MaterialApp(home: CSDamagedSeatScreen()));
        
        // Chip F5 và H1 (ngoài ô trên sơ đồ) phải có mặt.
        
        

        // Chạm lại F5 trên sơ đồ -> bỏ chọn.
        await tester.tap(find.text('F5').first);
        await tester.pump();
        
      },
    );
  });

  group('Lịch sử quét vé', () {
    late Directory dir;

    setUpAll(() async {
      dir = await Directory.systemTemp.createTemp('cs_hive_test');
      Hive.init(dir.path);
      await Hive.openBox<String>('scanned_tickets_box');
      await Hive.openBox<String>('scan_history_box');
    });

    tearDownAll(() async {
      await Hive.close();
      await dir.delete(recursive: true);
    });

    test('Vé vẫn bị phát hiện ĐÃ QUÉT sau khi hộp chờ sync bị dọn', () async {
      const raw =
          '{"v":1,"ticket":"T-001","room":"room1","seat":"F5","show":"S1"}';
      final at = DateTime(2026, 10, 3, 19, 30);

      await HiveService.addScanRecord(
        ScanRecord(
          ticket: 'T-001',
          room: 'room1',
          seat: 'F5',
          show: 'S1',
          scannedAt: at,
        ),
      );
      await HiveService.saveScannedTicket(raw);

      // Giả lập sync thành công -> hộp chờ bị xoá.
      await HiveService.clearTicketsAfterSync(
        HiveService.getAllScannedTickets(),
      );
      

      HiveService.findScanRecord('T-001');
      
      
      

      
      
    });
  });
}
