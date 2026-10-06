import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../core/database/hive_service.dart';
import '../../../core/network/api_client.dart';
import '../../../core/utils/time_format.dart';
import '../../../theme/app_theme.dart';
import '../../../mock/mock_data.dart';
import '../../../widgets/cs_app_card.dart';
import '../../../widgets/cs_scan_result_view.dart';
import '../../../screens/cs_scan_history_screen.dart';

class ScannerScreen extends StatefulWidget {
  final String roomId;
  final String showId;

  const ScannerScreen({
    super.key,
    this.roomId = 'room1',
    this.showId = '',
  });

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();

  String? lastScannedCode;
  bool isProcessing = false;

  CSMockMovie get _movie => CSMockData.movies.firstWhere(
        (m) => m.roomId == widget.roomId,
        orElse: () => CSMockData.movies.first,
      );

  /// Số vé đã soát thật (đọc từ lịch sử Hive) của phòng + suất hiện tại.
  int get _scannedCount => HiveService.getScanHistory(
        roomId: widget.roomId,
        showId: widget.showId,
      ).length;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }


  void _simulateScan(String payload) {
    if (isProcessing) return;
    setState(() => isProcessing = true);
    
    // Fake BarcodeCapture
    final mockBarcode = Barcode(rawValue: payload, format: BarcodeFormat.qrCode);
    final mockCapture = BarcodeCapture(barcodes: [mockBarcode]);
    
    // We delay slightly to simulate processing, then handle normally.
    // However, _handleBarcode is private and takes a BarcodeCapture.
    // Actually, we can just call _handleBarcode(mockCapture) but wait, we need to bypass isProcessing check there or just reset it.
    setState(() => isProcessing = false); 
    _handleBarcode(mockCapture);
  }

  void _handleBarcode(BarcodeCapture capture) async {
    if (isProcessing) return;

    final List<Barcode> barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      final code = barcode.rawValue;
      if (code != null) {
        setState(() => isProcessing = true);

        try {
          final Map<String, dynamic> data = jsonDecode(code);

          if (data['ticket'] == null ||
              data['room'] == null ||
              data['seat'] == null ||
              data['show'] == null) {
            _showResultBottomSheet(
              'LỖI DỮ LIỆU',
              type: CSScanResultType.invalid,
              title: 'MÃ KHÔNG HỢP LỆ',
              time: formatScanTime(DateTime.now()),
            );
            return;
          }

          if (data['room'] != widget.roomId) {
            _showResultBottomSheet(
              '${data["ticket"] ?? "KHÔNG RÕ"}',
              seat: '${data["seat"] ?? ""}',
              type: CSScanResultType.invalid,
              title: 'VÉ SAI PHÒNG',
              time: formatScanTime(DateTime.now()),
              customer: 'QR: ${data["room"]} - Rạp: ${widget.roomId}',
            );
            return;
          }

          if (widget.showId.isNotEmpty && data['show'] != widget.showId) {
            _showResultBottomSheet(
              '${data["ticket"] ?? "KHÔNG RÕ"}',
              seat: '${data["seat"] ?? ""}',
              type: CSScanResultType.invalid,
              title: 'VÉ SAI SUẤT',
              time: formatScanTime(DateTime.now()),
              customer: 'QR: ${data["show"]} - Suất: ${widget.showId}',
            );
            return;
          }

          final String ticketId = '${data['ticket']}';
          final String seat = '${data['seat']}';
          final String customer = '${data['customer'] ?? data['name'] ?? ''}';

          // Kiểm tra trùng bằng lịch sử vĩnh viễn
          final previous = HiveService.findScanRecord(ticketId);
          if (previous != null) {
            _showResultBottomSheet(
              ticketId,
              seat: seat,
              type: CSScanResultType.used,
              title: 'VÉ ĐÃ QUÉT',
              time: formatScanTime(previous.scannedAt),
              previousGate: 'Máy soát này · ${_movie.room}',
            );
            return;
          }

          final now = DateTime.now();
          await HiveService.addScanRecord(ScanRecord(
            ticket: ticketId,
            room: '${data['room']}',
            seat: seat,
            show: '${data['show']}',
            scannedAt: now,
          ));
          await HiveService.saveScannedTicket(code);

          ApiClient.syncTicketsToServer(widget.roomId, widget.showId).then((success) {
            if (success) {
              debugPrint("Đã bắn vé $ticketId lên server!");
            }
          });

          if (!mounted) return;
          setState(() {}); // cập nhật bộ đếm "Đã soát"

          _showResultBottomSheet(
            ticketId,
            seat: seat,
            type: CSScanResultType.success,
            title: 'QUÉT THÀNH CÔNG',
            time: formatScanTime(now),
            customer: customer,
          );
        } catch (e) {
          _showResultBottomSheet(
            'LỖI ĐỊNH DẠNG',
            type: CSScanResultType.invalid,
            title: 'MÃ KHÔNG HỢP LỆ',
            time: formatScanTime(DateTime.now()),
          );
        }
      }
    }
  }

  

  void _showResultBottomSheet(
    String ticketCode, {
    String seat = '',
    CSScanResultType type = CSScanResultType.success,
    String title = 'Soát vé thành công',
    String time = '',
    String customer = '',
    String previousGate = '',
  }) {
    final movie = _movie;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        return CSScanResultView(
          result: CSMockScanResult(
            type: type,
            title: title,
            seat: seat,
            quantity: '1 vé',
            customer: customer,
            ticketCode: ticketCode,
            usedAt: time,
            previousGate: previousGate,
            scanned: _scannedCount,
            total: movie.capacity,
          ),
          movie: movie,
          onScanNext: () => Navigator.pop(sheetContext),
        );
      },
    ).then((_) {
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) setState(() => isProcessing = false);
      });
    });
  }

  void _toggleFlash() {
    _controller.toggleTorch();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _handleBarcode,
          ),
          _ScannerOverlay(),
          Positioned(
            top: 40,
            left: 10,
            right: 10,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (Navigator.canPop(context))
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                    onPressed: () => Navigator.maybePop(context),
                  )
                else
                  const SizedBox(width: 48),
                IconButton(
                  icon: const Icon(Icons.flash_on, color: Colors.white),
                  onPressed: _toggleFlash,
                ),
              ],
            ),
          ),
          if (isProcessing)
            const Center(
              child: CircularProgressIndicator(),
            ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
              decoration: const BoxDecoration(
                color: CSAppColors.background,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Đưa mã QR vào khung hình',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  CSAppCard(
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _StatItem(
                          value: '$_scannedCount',
                          label: 'Đã soát',
                          color: CSAppColors.primary,
                        ),
                        Container(width: 1, height: 30, color: Colors.white24),
                        _StatItem(
                          value: '${_movie.capacity}',
                          label: 'Tổng vé',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => CSScanHistoryScreen(
                              roomId: widget.roomId,
                              showId: widget.showId,
                            ),
                          ),
                        );
                        if (mounted) setState(() {});
                      },
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white24),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                      child: const Text('Lịch sử quét'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ScannerOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final double width = constraints.maxWidth;
        final double scanArea = width * 0.7;

        return Stack(
          children: [
            Container(
              decoration: ShapeDecoration(
                shape: _ScannerHoleShape(
                  holeSize: Size(scanArea, scanArea),
                ),
              ),
            ),
            Center(
              child: Container(
                width: scanArea,
                height: scanArea,
                decoration: BoxDecoration(
                  border: Border.all(color: CSAppColors.primary, width: 2),
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ScannerHoleShape extends ShapeBorder {
  final Size holeSize;

  const _ScannerHoleShape({required this.holeSize});

  @override
  EdgeInsetsGeometry get dimensions => EdgeInsets.zero;

  @override
  Path getInnerPath(Rect rect, {TextDirection? textDirection}) => Path();

  @override
  Path getOuterPath(Rect rect, {TextDirection? textDirection}) {
    final holeRect = Rect.fromCenter(
      center: rect.center,
      width: holeSize.width,
      height: holeSize.height,
    );
    return Path()
      ..addRect(rect)
      ..addRRect(RRect.fromRectAndRadius(holeRect, const Radius.circular(12)))
      ..fillType = PathFillType.evenOdd;
  }

  @override
  void paint(Canvas canvas, Rect rect, {TextDirection? textDirection}) {
    final paint = Paint()
      ..color = Colors.black.withValues(alpha: 0.5)
      ..style = PaintingStyle.fill;
    canvas.drawPath(getOuterPath(rect), paint);
  }

  @override
  ShapeBorder scale(double t) => this;
}

class _StatItem extends StatelessWidget {
  final String value;
  final String label;
  final Color? color;

  const _StatItem({
    required this.value,
    required this.label,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: color ?? Colors.white,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: CSAppColors.muted,
          ),
        ),
      ],
    );
  }
}
