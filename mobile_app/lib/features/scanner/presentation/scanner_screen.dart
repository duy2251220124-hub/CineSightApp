import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../core/database/hive_service.dart';
import '../../../theme/app_theme.dart';
import '../../../mock/mock_data.dart';
import '../../../widgets/cs_app_card.dart';
import '../../../widgets/cs_scan_result_view.dart';
import '../../../screens/cs_scan_history_screen.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();

  // Biến dùng để debounce (chống quét liên tục cùng 1 mã)
  String? lastScannedCode;
  bool isProcessing = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

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

        _showResultBottomSheet(code);
      }
    }
  }

  void _showResultBottomSheet(String ticketCode) {
    // Gọi UI hiển thị kết quả từ Figma dưới dạng BottomSheet
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      enableDrag: false,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom,
          ),
          child: CSScanResultView(
            // Tạm thời hiển thị Mock Data nhưng gài mã vé thật vừa quét vào
            result: CSMockScanResult(
              type: CSScanResultType.success,
              title: 'QUÉT THÀNH CÔNG',
              seat: 'F12',
              quantity: '1 khách',
              customer: 'Khách hàng',
              ticketCode: ticketCode, // MÃ VÉ THẬT LẤY TỪ CAMERA
              usedAt: '',
              previousGate: '',
              scanned: 14,
              total: 120,
            ),
            movie: CSMockData.movies.first,
            onScanNext: () {
              Navigator.pop(context); // Đóng popup
              Future.delayed(const Duration(milliseconds: 500), () {
                if (mounted) {
                  setState(() => isProcessing = false);
                }
              });
            },
          ),
        );
      },
    );
  }

  void _toggleFlash() {
    _controller.toggleTorch();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black, // Nền đen cho UI camera quét
      body: SafeArea(
        child: Stack(
          children: [
            // 1. Camera View thực tế
            MobileScanner(controller: _controller, onDetect: _handleBarcode),

            // 2. Lớp phủ đen và khoét lỗ khung vuông (Viewfinder)
            Container(
              decoration: ShapeDecoration(
                shape: QrScannerOverlayShape(
                  borderColor: CSAppColors.primary,
                  borderRadius: 20,
                  borderLength: 40,
                  borderWidth: 3,
                  cutOutSize: 290,
                ),
              ),
            ),

            // 3. Các nút điều hướng Top Bar
            Positioned(
              top: 4,
              left: 8,
              child: IconButton(
                onPressed: () => Navigator.maybePop(context),
                icon: const Icon(Icons.chevron_left, color: Colors.white),
              ),
            ),
            Positioned(
              top: 4,
              right: 8,
              child: IconButton(
                onPressed: _toggleFlash,
                icon: const Icon(
                  Icons.flashlight_on_outlined,
                  color: Colors.white,
                ),
              ),
            ),

            // 4. Loading Indicator khi đang xử lý
            if (isProcessing)
              Container(
                color: Colors.black45,
                child: const Center(
                  child: CircularProgressIndicator(color: CSAppColors.primary),
                ),
              ),

            // 5. Bảng Thống kê & Nút chức năng ở dưới đáy (Figma Layout)
            Positioned(
              left: 16,
              right: 16,
              bottom: 18,
              child: CSAppCard(
                child: Column(
                  children: [
                    const Text(
                      'Đưa mã QR vào khung hình',
                      style: TextStyle(color: CSAppColors.muted),
                    ),
                    const SizedBox(height: 12),
                    const Row(
                      children: [
                        Expanded(
                          child: CSScanStat(
                            value: '13',
                            label: 'Đã soát',
                            color: CSAppColors.success,
                          ),
                        ),
                        SizedBox(width: 10),
                        Expanded(
                          child: CSScanStat(
                            value: '120',
                            label: 'Tổng vé',
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _toggleFlash,
                            icon: const Icon(Icons.flashlight_on_outlined),
                            label: const Text('Bật đèn'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: () {
                              // Chuyển sang màn hình Lịch sử quét (Nhóm C)
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (ctx) => CSScanHistoryScreen(
                                    
                                  )
                                )
                              );
                            },
                            icon: const Icon(Icons.search),
                            label: const Text('Tra cứu'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// --- CLASS PHỤ TRỢ: VẼ KHUNG QUÉT ---
class CSScanStat extends StatelessWidget {
  final String value;
  final String label;
  final Color color;

  const CSScanStat({
    super.key,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: CSAppColors.surfaceStrong,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 18,
              fontWeight: FontWeight.w800,
            ),
          ),
          Text(
            label,
            style: const TextStyle(color: CSAppColors.muted, fontSize: 10),
          ),
        ],
      ),
    );
  }
}

class QrScannerOverlayShape extends ShapeBorder {
  final Color borderColor;
  final double borderWidth;
  final double overlayColor;
  final double borderRadius;
  final double borderLength;
  final double cutOutSize;

  const QrScannerOverlayShape({
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
