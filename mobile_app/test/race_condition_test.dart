import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:mobile_app/core/database/hive_service.dart';

void main() {
  test('Race condition when syncing tickets', () async {
    Hive.init('test_hive_dir');
    await Hive.openBox<String>('scanned_tickets_box');
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
    debugPrint('Test passed! remainingTickets: ');
  });
}