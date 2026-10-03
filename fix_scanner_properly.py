import re

path = r'c:\CineSightApp\mobile_app\lib\features\scanner\presentation\scanner_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

def replace_handler(match):
    return """void _handleBarcode(BarcodeCapture capture) async {
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

  void _showError"""

content = re.sub(r'void _handleBarcode.*?void _showError', replace_handler, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement successful.")
