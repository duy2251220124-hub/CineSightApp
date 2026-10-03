enum CSScanResultType { success, wait, used, invalid }

class CSMockMovie {
  final String title;

  final String time;

  final String room;
  final String roomId;
  final String date;

  final String status;

  final int sold;

  final int capacity;

  const CSMockMovie({
    required this.title,

    required this.time,

    required this.room,
    required this.roomId,
    required this.date,

    required this.status,

    required this.sold,

    required this.capacity,
  });
}

class CSMockRoom {
  final String name;

  final String movie;

  final String time;

  final String status;

  const CSMockRoom({
    required this.name,

    required this.movie,

    required this.time,

    required this.status,
  });
}

class CSMockTicket {
  final String code;

  final String seat;

  final String scanTime;

  final String employee;

  final bool valid;

  const CSMockTicket({
    required this.code,

    required this.seat,

    required this.scanTime,

    required this.employee,

    required this.valid,
  });
}

class CSMockWarning {
  final String title;

  final String detail;

  final int severity;

  const CSMockWarning({
    required this.title,

    required this.detail,

    required this.severity,
  });
}

class CSMockIncident {
  final String title;

  final String reporter;

  final String description;

  final String room;

  final String position;

  final String time;

  final bool resolved;

  const CSMockIncident({
    required this.title,

    required this.reporter,

    required this.description,

    required this.room,

    required this.position,

    required this.time,

    required this.resolved,
  });
}

class CSMockNotification {
  final String title;

  final String detail;

  final String time;

  const CSMockNotification({
    required this.title,

    required this.detail,

    required this.time,
  });
}

class CSMockScanResult {
  final CSScanResultType type;

  final String title;

  final String seat;

  final String quantity;

  final String customer;

  final String ticketCode;

  final String usedAt;

  final String previousGate;

  final int scanned;

  final int total;

  const CSMockScanResult({
    required this.type,

    required this.title,

    required this.seat,

    required this.quantity,

    required this.customer,

    required this.ticketCode,

    required this.usedAt,

    required this.previousGate,

    required this.scanned,

    required this.total,
  });
}

abstract final class CSMockData {
  static const employeeName = 'Nguyen Van A';

  static const employeeId = 'US-221033';

  static const employeeRole = 'NhÃ¢n viÃªn váº­n hÃ nh';

  static const cinemaName = 'CGV Vinh Trung Plaza';

  static const shiftTime = '10:00 - 18:00';

  static const activeRooms = '5/5 phÃ²ng';

  static const selectedDate = '25/04';

  static const selectedDateLabel = 'HÃ´m nay, 25 ThÃ¡ng 4';

  static const movies = <CSMockMovie>[
    CSMockMovie(
      title: 'Kung Fu Panda 4',
      time: '19:30 - 21:20',
      room: 'PhÃ²ng 05',
      roomId: 'room1',
      date: '2026-09-29',
      status: 'ÄÃ£ phÃ¢n cÃ´ng: 1/2',
      sold: 96,
      capacity: 120,
    ),
    CSMockMovie(
      title: 'Dune: Part Two',
      time: '20:00 - 22:45',
      room: 'PhÃ²ng 01',
      roomId: 'room2',
      date: '2026-09-29',
      status: 'ÄÃ£ phÃ¢n cÃ´ng: 1/1',
      sold: 110,
      capacity: 120,
    ),
    CSMockMovie(
      title: 'Godzilla x Kong',
      time: '21:00 - 23:05',
      room: 'PhÃ²ng 03',
      roomId: 'room3',
      date: '2026-09-29',
      status: 'ChÆ°a phÃ¢n cÃ´ng: 0/1',
      sold: 84,
      capacity: 120,
    ),
  ];

  static const rooms = <CSMockRoom>[
    CSMockRoom(
      name: 'Ráº¡p 1',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Äang chiáº¿u',
    ),

    CSMockRoom(
      name: 'Ráº¡p 2',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Äang chiáº¿u',
    ),

    CSMockRoom(
      name: 'Ráº¡p 3',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Äang chiáº¿u',
    ),

    CSMockRoom(
      name: 'Ráº¡p 4',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Äang chiáº¿u',
    ),

    CSMockRoom(
      name: 'Ráº¡p 5',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Äang chiáº¿u',
    ),
  ];

  static const warnings = <CSMockWarning>[
    CSMockWarning(
      title: 'Gháº¿ cÃ³ ngÆ°á»i nhÆ°ng khÃ´ng cÃ³ vÃ©',

      detail: 'Ráº¡p 5: A10, A11 | HÃ ng B: B12',

      severity: 2,
    ),

    CSMockWarning(
      title: 'Gháº¿ cÃ³ ngÆ°á»i nhÆ°ng khÃ´ng cÃ³ vÃ©',

      detail: 'Ráº¡p 3: A10, A11 | HÃ ng B: B12',

      severity: 2,
    ),

    CSMockWarning(
      title: 'Gháº¿ cÃ³ vÃ© nhÆ°ng trá»‘ng ngÆ°á»i',

      detail: 'HÃ ng C: C08, C09',

      severity: 1,
    ),

    CSMockWarning(
      title: 'Gháº¿ cÃ³ vÃ© nhÆ°ng trá»‘ng ngÆ°á»i',

      detail: 'Sá»‘ lÆ°á»£ng ngÆ°á»i trong phÃ²ng vÆ°á»£t quÃ¡ sá»‘ vÃ© soÃ¡t',

      severity: 0,
    ),
  ];

  static const tickets = <CSMockTicket>[
    CSMockTicket(
      code: 'TICK-8842',

      seat: 'C04',

      scanTime: '19:15',

      employee: 'Báº¡n',

      valid: true,
    ),

    CSMockTicket(
      code: 'TICK-8842',

      seat: 'C04',

      scanTime: '19:15',

      employee: 'Báº¡n',

      valid: false,
    ),

    CSMockTicket(
      code: 'TICK-8843',

      seat: 'C05',

      scanTime: '19:16',

      employee: 'Báº¡n',

      valid: true,
    ),

    CSMockTicket(
      code: 'TICK-8844',

      seat: 'C06',

      scanTime: '19:17',

      employee: 'Báº¡n',

      valid: true,
    ),
  ];

  static const incidents = <CSMockIncident>[
    CSMockIncident(
      title: 'Gháº¿ C4 - RÃ¡ch Ä‘á»‡m gháº¿',

      reporter: 'NV_Tuan (Ca trÆ°á»›c)',

      description: 'Äá»‡m mÃºt rÃ¡ch lá»™ pháº§n khung sáº¯t bÃªn trong, cÃ³ thá»ƒ gÃ¢y máº¥t an toÃ n hoáº·c rÃ¡ch quáº§n Ã¡o cá»§a khÃ¡ch hÃ ng khi ngá»“i.',

      room: 'Ráº¡p 3',

      position: 'HÃ ng C - Gháº¿ 04',

      time: '14:00 - 24/09/2026',

      resolved: false,
    ),

    CSMockIncident(
      title: 'Báº­c thá»m F - ChÃ¡y Ä‘Ã¨n LED',

      reporter: 'Báº¡n (15 phÃºt trÆ°á»›c)',

      description: 'ÄÃ¨n LED chá»‰ dáº«n lá»‘i Ä‘i hÃ ng F bá»‹ máº¥t nguá»“n hoÃ n toÃ n.',

      room: 'Ráº¡p 3',

      position: 'Báº­c thá»m F',

      time: '15 phÃºt trÆ°á»›c',

      resolved: false,
    ),

    CSMockIncident(
      title: 'MÃ¡y láº¡nh rá»‰ nÆ°á»›c gÃ³c tÆ°á»ng',

      reporter: 'Ká»¹ thuáº­t',

      description: 'ÄÃ£ thÃ´ng Ä‘Æ°á»ng á»‘ng thoÃ¡t nÆ°á»›c mÃ¡y láº¡nh gÃ³c phÃ­a TÃ¢y.',

      room: 'Ráº¡p 3',

      position: 'GÃ³c phÃ­a TÃ¢y',

      time: '14:30',

      resolved: true,
    ),
  ];

  static const notifications = <CSMockNotification>[
    CSMockNotification(
      title: 'Sá»± cá»‘ má»›i phÃ¡t sinh - Ráº¡p 3',

      detail: 'Gháº¿ C4 rÃ¡ch Ä‘á»‡m bá»c da, cáº§n ká»¹ thuáº­t xá»­ lÃ½ gáº¥p trÆ°á»›c ca tá»‘i.',

      time: '15 phÃºt trÆ°á»›c',
    ),

    CSMockNotification(
      title: 'Äá»•i ca bÃ n giao ca lÃ m',

      detail: 'NV_Tuan Ä‘Ã£ gá»­i bÃ¡o cÃ¡o bÃ n giao ca chiá»u.',

      time: '1 giá» trÆ°á»›c',
    ),

    CSMockNotification(
      title: 'Báº¯t Ä‘áº§u suáº¥t chiáº¿u: Dune 2',

      detail: 'Suáº¥t chiáº¿u phÃ²ng 1 Ä‘Ã£ báº¯t Ä‘áº§u lÃºc 20:00.',

      time: '2 giá» trÆ°á»›c',
    ),
  ];

  static const scanSuccess = CSMockScanResult(
    type: CSScanResultType.success,

    title: 'QUÃ‰T THÃ€NH CÃ”NG',

    seat: 'F12',

    quantity: '1 khÃ¡ch',

    customer: 'Nguyá»…n VÄƒn A',

    ticketCode: '#4823',

    usedAt: '',

    previousGate: '',

    scanned: 13,

    total: 120,
  );

  static const scanWait = CSMockScanResult(
    type: CSScanResultType.wait,

    title: 'VUI LÃ’NG CHá»œ',

    seat: 'F12',

    quantity: '1 khÃ¡ch',

    customer: '',

    ticketCode: '#4823',

    usedAt: '19:13 - 24/04/2026',

    previousGate: 'Táº¡i Cá»•ng 2',

    scanned: 28,

    total: 120,
  );

  static const scanUsed = CSMockScanResult(
    type: CSScanResultType.used,

    title: 'VÃ‰ ÄÃƒ QUÃ‰T',

    seat: 'F12',

    quantity: '1 khÃ¡ch',

    customer: '',

    ticketCode: '#4823',

    usedAt: '19:13 - 24/04/2026',

    previousGate: 'Táº¡i Cá»•ng 2',

    scanned: 28,

    total: 120,
  );

  static const occupiedSeats = <String>[
    'C1',
    'C2',
    'C3',
    'C4',
    'C5',
    'C6',
    'C7',
    'C8',

    'D1',
    'D2',
    'D5',
    'D6',
    'D7',
    'D8',

    'E1',
    'E2',
    'E3',
    'E4',
    'E5',
    'E6',
    'E7',
    'E8',

    'F1',
    'F2',
    'F3',
    'F4',
    'F7',
    'F8',

    'G1',
    'G2',
    'G3',
    'G4',
    'G5',
    'G6',
    'G7',
    'G8',

    'H1',
    'H2',
    'H3',
    'H4',
    'H5',
    'H6',
    'H7',
    'H8',
  ];

  static const brokenSeats = <String>['F5', 'F6'];

  static const warningSeats = <String>['D3', 'D4'];
}
