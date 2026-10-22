import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:mobile_app/core/database/hive_service.dart';

void main() {
  late Directory tempDir;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('hive_test_race_');
    Hive.init(tempDir.path);
    await Hive.openBox<String>('scanned_tickets_box');
    await Hive.openBox<String>('scan_history_box');
  });

  tearDown(() async {
    await Hive.close();
    if (tempDir.existsSync()) {
      tempDir.deleteSync(recursive: true);
    }
  });

  test('Race condition when syncing tickets', () async {
    await HiveService.saveScannedTicket('ticket_1');
    await HiveService.saveScannedTicket('ticket_2');
    
    final snapshotToSync = HiveService.getAllScannedTickets();
    expect(snapshotToSync.length, 2);
    
    await HiveService.saveScannedTicket('ticket_3');
    expect(HiveService.getAllScannedTickets().length, 3);
    
    await HiveService.clearTicketsAfterSync(snapshotToSync);
    final remainingTickets = HiveService.getAllScannedTickets();
    
    expect(remainingTickets.length, 1);
    expect(remainingTickets.first, 'ticket_3');
    debugPrint('Test passed! remainingTickets: ${remainingTickets.length}');
  });
}
