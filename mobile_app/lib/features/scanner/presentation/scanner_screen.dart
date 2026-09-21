import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../../core/database/hive_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  // Biến dùng để debounce (chống quét liên tục cùng 1 mã)
  String? lastScannedCode;
  bool isProcessing = false;

  void _handleBarcode(BarcodeCapture capture) async {
    if (isProcessing) return;

    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isNotEmpty) {
      final String code = barcodes.first.rawValue ?? '';

      if (code.isNotEmpty && code != lastScannedCode) {
        setState(() {
          isProcessing = true;
          lastScannedCode = code;
        });

        // --- TÍCH HỢP HIVE DATABASE TẠI ĐÂY ---
        // Lưu ngay lập tức mã vé vừa quét vào ổ cứng điện thoại (Lưu Offline)
        await HiveService.saveScannedTicket(code);

        _showResultDialog(code);
      }
    }
  }

  void _showResultDialog(String ticketCode) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return AlertDialog(
          title: const Text(
            'Soát vé thành công',
            style: TextStyle(color: Colors.green),
          ),
          content: Text(
            'Mã vé: $ticketCode\n\nTrạng thái: ĐÃ LƯU OFFLINE VÀO MÁY (Tập A).',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                Future.delayed(const Duration(seconds: 2), () {
                  if (mounted) {
                    setState(() {
                      isProcessing = false;
                    });
                  }
                });
              },
              child: const Text('Tiếp tục quét'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Soát vé rạp phim'),
        actions: [
          IconButton(
            icon: const Icon(Icons.sync, color: Colors.greenAccent),
            tooltip: 'Kiểm tra vé đang lưu',
            onPressed: () {
              // Test thử tính năng lấy toàn bộ vé đang lưu Offline trong máy
              final list = HiveService.getAllScannedTickets();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    'Đang có ${list.length} vé trong máy chờ đồng bộ lên AI!',
                  ),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.edit_note),
            tooltip: 'Nhập tay',
            onPressed: () {},
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            onDetect: _handleBarcode,
            overlayBuilder: (context, constraints) {
              return Container(
                decoration: ShapeDecoration(
                  shape: QrScannerOverlayShape(
                    borderColor: Colors.redAccent,
                    borderRadius: 10,
                    borderLength: 30,
                    borderWidth: 8,
                    cutOutSize: MediaQuery.of(context).size.width * 0.7,
                  ),
                ),
              );
            },
          ),
          if (isProcessing)
            Container(
              color: Colors.black45,
              child: const Center(
                child: CircularProgressIndicator(color: Colors.white),
              ),
            ),
        ],
      ),
    );
  }
}

// Class phụ trợ: Vẽ khung vuông ở giữa màn hình (Viewfinder)
class QrScannerOverlayShape extends ShapeBorder {
  final Color borderColor;
  final double borderWidth;
  final double overlayColor;
  final double borderRadius;
  final double borderLength;
  final double cutOutSize;

  QrScannerOverlayShape({
    this.borderColor = Colors.red,
    this.borderWidth = 3.0,
    this.overlayColor = 150,
    this.borderRadius = 0,
    this.borderLength = 40,
    this.cutOutSize = 250,
  });

  @override
  EdgeInsetsGeometry get dimensions => const EdgeInsets.all(10.0);

  @override
  Path getInnerPath(Rect rect, {TextDirection? textDirection}) {
    return Path()
      ..fillType = PathFillType.evenOdd
      ..addPath(getOuterPath(rect), Offset.zero);
  }

  @override
  Path getOuterPath(Rect rect, {TextDirection? textDirection}) {
    Path path = Path()..addRect(rect);
    rect = Rect.fromCenter(
      center: rect.center,
      width: cutOutSize,
      height: cutOutSize,
    );
    path.addRRect(RRect.fromRectAndRadius(rect, Radius.circular(borderRadius)));
    return path;
  }

  @override
  void paint(Canvas canvas, Rect rect, {TextDirection? textDirection}) {
    final backgroundPaint = Paint()
      ..color = Colors.black.withAlpha(overlayColor.toInt())
      ..style = PaintingStyle.fill;
    final cutOutRect = Rect.fromCenter(
      center: rect.center,
      width: cutOutSize,
      height: cutOutSize,
    );
    final borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = borderWidth;
    canvas.drawPath(
      Path.combine(
        PathOperation.difference,
        Path()..addRect(rect),
        Path()..addRRect(
          RRect.fromRectAndRadius(cutOutRect, Radius.circular(borderRadius)),
        ),
      ),
      backgroundPaint,
    );
    final path = Path();
    final double left = cutOutRect.left,
        right = cutOutRect.right,
        top = cutOutRect.top,
        bottom = cutOutRect.bottom;
    path.moveTo(left, top + borderLength);
    path.lineTo(left, top);
    path.lineTo(left + borderLength, top);
    path.moveTo(right - borderLength, top);
    path.lineTo(right, top);
    path.lineTo(right, top + borderLength);
    path.moveTo(right, bottom - borderLength);
    path.lineTo(right, bottom);
    path.lineTo(right - borderLength, bottom);
    path.moveTo(left + borderLength, bottom);
    path.lineTo(left, bottom);
    path.lineTo(left, bottom - borderLength);
    canvas.drawPath(path, borderPaint);
  }

  @override
  ShapeBorder scale(double t) {
    return QrScannerOverlayShape(
      borderColor: borderColor,
      borderWidth: borderWidth,
      overlayColor: overlayColor,
    );
  }
}
