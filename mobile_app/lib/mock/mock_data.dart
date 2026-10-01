

enum CSScanResultType { success, wait, used }



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

  static const employeeRole = 'Nhân viên vận hành';

  static const cinemaName = 'CGV Vinh Trung Plaza';

  static const shiftTime = '10:00 - 18:00';

  static const activeRooms = '5/5 phòng';

  static const selectedDate = '25/04';

  static const selectedDateLabel = 'Hôm nay, 25 Tháng 4';



  static const movies = <CSMockMovie>[
    CSMockMovie(
      title: 'Kung Fu Panda 4',
      time: '19:30 - 21:20',
      room: 'Phòng 05',
      roomId: 'room1',
      date: '2026-09-29',
      status: 'Đã phân công: 1/2',
      sold: 96,
      capacity: 120,
    ),
    CSMockMovie(
      title: 'Dune: Part Two',
      time: '20:00 - 22:45',
      room: 'Phòng 01',
      roomId: 'room2',
      date: '2026-09-29',
      status: 'Đã phân công: 1/1',
      sold: 110,
      capacity: 120,
    ),
    CSMockMovie(
      title: 'Godzilla x Kong',
      time: '21:00 - 23:05',
      room: 'Phòng 03',
      roomId: 'room3',
      date: '2026-09-29',
      status: 'Chưa phân công: 0/1',
      sold: 84,
      capacity: 120,
    ),
];



  static const rooms = <CSMockRoom>[

    CSMockRoom(

      name: 'Rạp 1',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Đang chiếu',

    ),

    CSMockRoom(

      name: 'Rạp 2',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Đang chiếu',

    ),

    CSMockRoom(

      name: 'Rạp 3',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Đang chiếu',

    ),

    CSMockRoom(

      name: 'Rạp 4',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Đang chiếu',

    ),

    CSMockRoom(

      name: 'Rạp 5',

      movie: 'Kung Fu Panda 4',

      time: '19:30 - 21:20',

      status: 'Đang chiếu',

    ),

  ];



  static const warnings = <CSMockWarning>[

    CSMockWarning(

      title: 'Ghế có người nhưng không có vé',

      detail: 'Rạp 5: A10, A11 | Hàng B: B12',

      severity: 2,

    ),

    CSMockWarning(

      title: 'Ghế có người nhưng không có vé',

      detail: 'Rạp 3: A10, A11 | Hàng B: B12',

      severity: 2,

    ),

    CSMockWarning(

      title: 'Ghế có vé nhưng trống người',

      detail: 'Hàng C: C08, C09',

      severity: 1,

    ),

    CSMockWarning(

      title: 'Vượt quá sức chứa',

      detail: 'Số lượng người trong phòng vượt quá số vé soát',

      severity: 0,

    ),

  ];



  static const tickets = <CSMockTicket>[

    CSMockTicket(

      code: 'TICK-8842',

      seat: 'C04',

      scanTime: '19:15',

      employee: 'Bạn',

      valid: true,

    ),

    CSMockTicket(

      code: 'TICK-8842',

      seat: 'C04',

      scanTime: '19:15',

      employee: 'Bạn',

      valid: false,

    ),

    CSMockTicket(

      code: 'TICK-8843',

      seat: 'C05',

      scanTime: '19:16',

      employee: 'Bạn',

      valid: true,

    ),

    CSMockTicket(

      code: 'TICK-8844',

      seat: 'C06',

      scanTime: '19:17',

      employee: 'Bạn',

      valid: true,

    ),

  ];



  static const incidents = <CSMockIncident>[

    CSMockIncident(

      title: 'Ghế C4 - Rách đệm ghế',

      reporter: 'NV_Tuan (Ca trước)',

      description:

          'Đệm mút rách lộ phần khung sắt bên trong, có thể gây mất an toàn hoặc rách quần áo của khách hàng khi ngồi.',

      room: 'Rạp 3',

      position: 'Hàng C - Ghế 04',

      time: '14:00 - 24/09/2026',

      resolved: false,

    ),

    CSMockIncident(

      title: 'Bậc thềm F - Cháy đèn LED',

      reporter: 'Bạn (15 phút trước)',

      description:

          'Đèn LED chỉ dẫn lối đi hàng F bị mất nguồn hoàn toàn.',

      room: 'Rạp 3',

      position: 'Bậc thềm F',

      time: '15 phút trước',

      resolved: false,

    ),

    CSMockIncident(

      title: 'Máy lạnh rỉ nước góc tường',

      reporter: 'Kỹ thuật',

      description:

          'Đã thông đường ống thoát nước máy lạnh góc phía Tây.',

      room: 'Rạp 3',

      position: 'Góc phía Tây',

      time: '14:30',

      resolved: true,

    ),

  ];



  static const notifications = <CSMockNotification>[

    CSMockNotification(

      title: 'Sự cố mới phát sinh - Rạp 3',

      detail:

          'Ghế C4 rách đệm bọc da, cần kỹ thuật xử lý gấp trước ca tối.',

      time: '15 phút trước',

    ),

    CSMockNotification(

      title: 'Đổi ca bàn giao ca làm',

      detail: 'NV_Tuan đã gửi báo cáo bàn giao ca chiều.',

      time: '1 giờ trước',

    ),

    CSMockNotification(

      title: 'Bắt đầu suất chiếu: Dune 2',

      detail: 'Suất chiếu phòng 1 đã bắt đầu lúc 20:00.',

      time: '2 giờ trước',

    ),

  ];



  static const scanSuccess = CSMockScanResult(

    type: CSScanResultType.success,

    title: 'QUÉT THÀNH CÔNG',

    seat: 'F12',

    quantity: '1 khách',

    customer: 'Nguyễn Văn A',

    ticketCode: '#4823',

    usedAt: '',

    previousGate: '',

    scanned: 13,

    total: 120,

  );



  static const scanWait = CSMockScanResult(

    type: CSScanResultType.wait,

    title: 'VUI LÒNG CHỜ',

    seat: 'F12',

    quantity: '1 khách',

    customer: '',

    ticketCode: '#4823',

    usedAt: '19:13 - 24/04/2026',

    previousGate: 'Tại Cổng 2',

    scanned: 28,

    total: 120,

  );



  static const scanUsed = CSMockScanResult(

    type: CSScanResultType.used,

    title: 'VÉ ĐÃ QUÉT',

    seat: 'F12',

    quantity: '1 khách',

    customer: '',

    ticketCode: '#4823',

    usedAt: '19:13 - 24/04/2026',

    previousGate: 'Tại Cổng 2',

    scanned: 28,

    total: 120,

  );



  static const occupiedSeats = <String>[

    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8',

    'D1', 'D2', 'D5', 'D6', 'D7', 'D8',

    'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8',

    'F1', 'F2', 'F3', 'F4', 'F7', 'F8',

    'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8',

    'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8',

  ];



  static const brokenSeats = <String>['F5', 'F6'];

  static const warningSeats = <String>['D3', 'D4'];

  static const selectedBrokenSeats = <String>['F5', 'H1'];

}






