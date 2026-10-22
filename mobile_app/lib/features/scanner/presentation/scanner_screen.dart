import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../core/database/hive_service.dart';
import '../../../core/network/api_client.dart';
import '../../../core/utils/time_format.dart';
import '../../../core/utils/show_id_utils.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/models/scan_models.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/features/scanner/presentation/widgets/cs_scan_result_view.dart';
import 'package:mobile_app/features/scanner/presentation/cs_scan_history_screen.dart';

class ScannerScreen extends StatefulWidget {
  final String roomId;
  final String showId;
  final void Function(String roomId, String showId)? onShowtimeChanged;

  const ScannerScreen({
    super.key,
    this.roomId = 'room1',
    this.showId = '',
    this.onShowtimeChanged,
  });

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();

  late String _activeRoomId;
  late String _activeShowId;
  String _activeMovieTitle = '';
  List<Map<String, dynamic>> _availableShowtimes = [];
  bool _isLoadingShowtimes = false;
  bool _isAutoMode = false;

  String? lastScannedCode;
  bool isProcessing = false;

  @override
  void initState() {
    super.initState();
    _activeRoomId = widget.roomId.isNotEmpty ? widget.roomId : CSActiveShowtime.roomId;
    _activeShowId = widget.showId.isNotEmpty ? widget.showId : CSActiveShowtime.showId;
    _activeMovieTitle = CSActiveShowtime.movieTitle;
    if (_activeShowId == 'all') {
      _isAutoMode = true;
    }

    CSActiveShowtime.notifier.addListener(_onGlobalShowtimeChanged);
    _loadShowtimes();
  }

  @override
  void dispose() {
    CSActiveShowtime.notifier.removeListener(_onGlobalShowtimeChanged);
    _controller.dispose();
    super.dispose();
  }

  void _onGlobalShowtimeChanged() {
    if (!mounted) return;
    final newRoom = CSActiveShowtime.roomId;
    final newShow = CSActiveShowtime.showId;
    final newTitle = CSActiveShowtime.movieTitle;

    if (newRoom != _activeRoomId || newShow != _activeShowId) {
      setState(() {
        _activeRoomId = newRoom;
        _activeShowId = newShow;
        _activeMovieTitle = newTitle;
        _isAutoMode = (newShow == 'all');
      });
      _loadShowtimes();
    }
  }

  Future<void> _loadShowtimes({VoidCallback? onDone}) async {
    setState(() => _isLoadingShowtimes = true);
    try {
      final list = await ApiClient.fetchShowtimes(roomId: _activeRoomId);
      if (!mounted) return;
      if (list.isNotEmpty) {
        final parsed = list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        setState(() {
          _availableShowtimes = parsed;
          _isLoadingShowtimes = false;
        });
        _resolveActiveShowTitle();
      } else {
        setState(() => _isLoadingShowtimes = false);
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingShowtimes = false);
    } finally {
      onDone?.call();
    }
  }

  void _resolveActiveShowTitle() {
    if (_isAutoMode) {
      _activeMovieTitle = 'Tất cả suất (Tự động)';
      return;
    }

    if (_activeShowId.isEmpty) {
      final match2010 = _availableShowtimes.firstWhere(
        (s) => '${s['show_id']}'.contains('20:10'),
        orElse: () => _availableShowtimes.isNotEmpty ? _availableShowtimes.first : {},
      );
      if (match2010.isNotEmpty) {
        setState(() {
          _activeShowId = '${match2010['show_id']}';
          _activeMovieTitle = '${match2010['movie_name'] ?? match2010['title'] ?? ''}';
        });
      }
      return;
    }

    final found = _availableShowtimes.firstWhere(
      (s) =>
          '${s['show_id']}' == _activeShowId ||
          ('${s['show_id']}'.contains('T') &&
              _activeShowId.contains('T') &&
              '${s['show_id']}'.split('T')[1] == _activeShowId.split('T')[1]),
      orElse: () => {},
    );
    if (found.isNotEmpty) {
      setState(() {
        _activeMovieTitle = '${found['movie_name'] ?? found['title'] ?? ''}';
      });
    }
  }

  String _formatRoomName(String rId) {
    final clean = rId.replaceAll('seats_config_', '').trim();
    final num = clean.replaceAll('room', '').trim();
    return num.isNotEmpty && int.tryParse(num) != null ? 'Phòng $num' : clean;
  }

  String _formatTimeDisplay(String sId) {
    if (sId == 'all' || sId.isEmpty) return 'Tất cả suất';
    if (sId.contains('T')) {
      return sId.split('T')[1];
    }
    return sId;
  }

  String _getHeaderTitle() {
    final roomName = _formatRoomName(_activeRoomId);
    if (_isAutoMode) {
      return '$roomName · ⚡ Tự động nhận diện';
    }
    final timeStr = _formatTimeDisplay(_activeShowId);
    if (_activeMovieTitle.isNotEmpty) {
      return '$roomName · $timeStr ($_activeMovieTitle)';
    }
    return '$roomName · Suất $timeStr';
  }

  CSMockMovie get _movie => CSMockMovie(
        id: '1',
        title: _isAutoMode
            ? 'Tất cả suất'
            : (_activeMovieTitle.isNotEmpty ? _activeMovieTitle : 'Đang kiểm vé'),
        time: _isAutoMode ? 'Tự động' : _formatTimeDisplay(_activeShowId),
        room: _activeRoomId,
        roomId: _activeRoomId,
        showId: _activeShowId,
      );

  /// Số vé đã soát thật (đọc từ lịch sử Hive) của phòng + suất hiện tại.
  int get _scannedCount => HiveService.getScanHistory(
        roomId: _activeRoomId,
        showId: _isAutoMode ? null : _activeShowId,
      ).length;

  void _selectShowtime(String showId, String movieTitle, {required bool isAuto}) {
    setState(() {
      _isAutoMode = isAuto;
      _activeShowId = showId;
      _activeMovieTitle = movieTitle;
    });

    CSActiveShowtime.update(
      roomId: _activeRoomId,
      showId: _activeShowId,
      movieTitle: _activeMovieTitle,
    );

    widget.onShowtimeChanged?.call(_activeRoomId, _activeShowId);

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          isAuto
              ? 'Đã bật chế độ tự động nhận diện cho ${_formatRoomName(_activeRoomId)}'
              : 'Đã khóa cổng soát: ${_formatRoomName(_activeRoomId)} · ${_formatTimeDisplay(_activeShowId)} ($movieTitle)',
        ),
        backgroundColor: CSAppColors.surfaceStrong,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _openShowtimePickerModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetCtx) {
        return StatefulBuilder(
          builder: (modalCtx, setModalState) {
            final rooms = [
              {'id': 'room1', 'name': 'Phòng 1'},
              {'id': 'room2', 'name': 'Phòng 2'},
              {'id': 'room3', 'name': 'Phòng 3'},
              {'id': 'room4', 'name': 'Phòng 4'},
            ];

            return Container(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(sheetCtx).size.height * 0.85,
              ),
              decoration: const BoxDecoration(
                color: Color(0xFF141824),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.only(bottom: 14),
                      decoration: BoxDecoration(
                        color: Colors.white24,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Cấu hình cổng soát vé',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Colors.white70, size: 20),
                        onPressed: () => Navigator.pop(sheetCtx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'PHÒNG CHIẾU',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.1,
                      color: CSAppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: rooms.map((r) {
                      final isSelected = _activeRoomId == r['id'];
                      return ChoiceChip(
                        label: Text(
                          r['name']!,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: isSelected ? Colors.white : Colors.white70,
                          ),
                        ),
                        selected: isSelected,
                        selectedColor: CSAppColors.primary,
                        backgroundColor: const Color(0xFF1F2638),
                        onSelected: (val) {
                          if (val && _activeRoomId != r['id']) {
                            setState(() {
                              _activeRoomId = r['id']!;
                            });
                            setModalState(() {});
                            _loadShowtimes(onDone: () => setModalState(() {}));
                          }
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'CHẾ ĐỘ SOÁT VÉ',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.1,
                      color: CSAppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Chế độ Tự động
                  InkWell(
                    onTap: () {
                      _selectShowtime('all', 'Tất cả suất hôm nay (Tự động)', isAuto: true);
                      Navigator.pop(sheetCtx);
                    },
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _isAutoMode
                            ? CSAppColors.primary.withValues(alpha: 0.15)
                            : const Color(0xFF1B2234),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _isAutoMode ? CSAppColors.primary : Colors.white12,
                          width: _isAutoMode ? 1.5 : 1,
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: CSAppColors.primary.withValues(alpha: 0.2),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.flash_auto,
                                color: CSAppColors.primary, size: 20),
                          ),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '⚡ Tự động nhận diện (Tất cả suất)',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                    color: Colors.white,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'Chấp nhận mọi vé đúng phòng, tự khớp theo suất trên vé',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: CSAppColors.muted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (_isAutoMode)
                            const Icon(Icons.check_circle,
                                color: CSAppColors.primary, size: 22),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  const Text(
                    'HOẶC KHÓA THEO SUẤT CHIẾU CỤ THỂ:',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.1,
                      color: CSAppColors.muted,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Expanded(
                    child: _isLoadingShowtimes
                        ? const Center(child: CircularProgressIndicator())
                        : _availableShowtimes.isEmpty
                            ? const Center(
                                child: Text(
                                  'Không tìm thấy lịch chiếu cho phòng này',
                                  style: TextStyle(color: CSAppColors.muted),
                                ),
                              )
                            : ListView.separated(
                                itemCount: _availableShowtimes.length,
                                separatorBuilder: (_, _) =>
                                    const SizedBox(height: 8),
                                itemBuilder: (context, idx) {
                                  final s = _availableShowtimes[idx];
                                  final showId = '${s['show_id']}';
                                  final movieName =
                                      '${s['movie_name'] ?? s['title'] ?? 'Suất chiếu'}';
                                  final startTime = '${s['start_time'] ?? ''}';
                                  final endTime = '${s['end_time'] ?? ''}';
                                  final date = '${s['date'] ?? ''}';

                                  final isCurrent = !_isAutoMode &&
                                      (_activeShowId == showId ||
                                          (_activeShowId.contains('T') &&
                                              showId.contains('T') &&
                                              _activeShowId.split('T')[1] ==
                                                  showId.split('T')[1]));

                                  return InkWell(
                                    onTap: () {
                                      _selectShowtime(showId, movieName,
                                          isAuto: false);
                                      Navigator.pop(sheetCtx);
                                    },
                                    borderRadius: BorderRadius.circular(10),
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 12, vertical: 10),
                                      decoration: BoxDecoration(
                                        color: isCurrent
                                            ? CSAppColors.primary
                                                .withValues(alpha: 0.15)
                                            : const Color(0xFF1A2132),
                                        borderRadius:
                                            BorderRadius.circular(10),
                                        border: Border.all(
                                          color: isCurrent
                                              ? CSAppColors.primary
                                              : Colors.white10,
                                          width: isCurrent ? 1.5 : 1,
                                        ),
                                      ),
                                      child: Row(
                                        children: [
                                          Container(
                                            padding:
                                                const EdgeInsets.symmetric(
                                                    horizontal: 8,
                                                    vertical: 4),
                                            decoration: BoxDecoration(
                                              color: isCurrent
                                                  ? CSAppColors.primary
                                                  : const Color(0xFF283248),
                                              borderRadius:
                                                  BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              startTime.isNotEmpty
                                                  ? startTime
                                                  : showId.split('T').last,
                                              style: TextStyle(
                                                color: isCurrent
                                                    ? Colors.black
                                                    : Colors.white,
                                                fontWeight: FontWeight.bold,
                                                fontSize: 13,
                                              ),
                                            ),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  movieName,
                                                  maxLines: 1,
                                                  overflow:
                                                      TextOverflow.ellipsis,
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.w600,
                                                    fontSize: 13,
                                                    color: Colors.white,
                                                  ),
                                                ),
                                                const SizedBox(height: 2),
                                                Text(
                                                  '$date · Đến $endTime',
                                                  style: const TextStyle(
                                                    fontSize: 11,
                                                    color: CSAppColors.muted,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                          if (isCurrent)
                                            const Icon(Icons.check_circle,
                                                color: CSAppColors.primary,
                                                size: 20),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
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

          final String ticketRoom =
              '${data['room']}'.replaceAll('seats_config_', '').trim();
          final String currentRoom =
              _activeRoomId.replaceAll('seats_config_', '').trim();

          if (ticketRoom != currentRoom) {
            _showResultBottomSheet(
              '${data["ticket"] ?? "KHÔNG RÕ"}',
              seat: '${data["seat"] ?? ""}',
              type: CSScanResultType.invalid,
              title: 'VÉ SAI PHÒNG',
              time: formatScanTime(DateTime.now()),
              customer:
                  'QR: ${data["room"]} - Cổng soát: ${_formatRoomName(currentRoom)}',
            );
            return;
          }

          // Kiểm tra Suất Chiếu
          final String ticketShow = '${data['show']}'.trim();
          final String ticketTime =
              ticketShow.contains('T') ? ticketShow.split('T')[1] : ticketShow;
          final String activeTime = _activeShowId.contains('T')
              ? _activeShowId.split('T')[1]
              : _activeShowId;

          bool isShowtimeValid = false;
          if (_isAutoMode || _activeShowId == 'all' || _activeShowId.isEmpty) {
            isShowtimeValid = true;
          } else {
            if (ticketShow == _activeShowId || ticketTime == activeTime) {
              isShowtimeValid = true;
            }
          }

          if (!isShowtimeValid) {
            _showResultBottomSheet(
              '${data["ticket"] ?? "KHÔNG RÕ"}',
              seat: '${data["seat"] ?? ""}',
              type: CSScanResultType.invalid,
              title: 'VÉ SAI SUẤT',
              time: formatScanTime(DateTime.now()),
              customer: 'QR: $ticketTime - Cổng soát: $activeTime',
            );
            return;
          }

          final String ticketId = '${data['ticket']}';
          final String seat = '${data['seat']}';
          final String customer = '${data['customer'] ?? data['name'] ?? ''}';

          // Kiểm tra trùng bằng lịch sử vĩnh viễn (anti-passback)
          final previous = HiveService.findScanRecord(ticketId);
          if (previous != null) {
            _showResultBottomSheet(
              ticketId,
              seat: seat,
              type: CSScanResultType.used,
              title: 'VÉ ĐÃ QUÉT',
              time: formatScanTime(previous.scannedAt),
              previousGate: 'Máy soát này · ${_formatRoomName(currentRoom)}',
            );
            return;
          }

          final now = DateTime.now();
          final actualShowToRecord =
              ticketShow.isNotEmpty ? ticketShow : _activeShowId;

          await HiveService.addScanRecord(ScanRecord(
            ticket: ticketId,
            room: currentRoom,
            seat: seat,
            show: actualShowToRecord,
            scannedAt: now,
          ));
          await HiveService.saveScannedTicket(code);

          ApiClient.syncTicketsToServer(currentRoom, actualShowToRecord)
              .then((success) {
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

          // Thanh điều hướng & chọn suất chiếu trên đỉnh
          Positioned(
            top: 40,
            left: 12,
            right: 12,
            child: Row(
              children: [
                if (Navigator.canPop(context))
                  IconButton(
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                    onPressed: () => Navigator.maybePop(context),
                  )
                else
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.55),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.qr_code_scanner,
                        color: CSAppColors.primary, size: 20),
                  ),
                const SizedBox(width: 8),
                Expanded(
                  child: InkWell(
                    onTap: _openShowtimePickerModal,
                    borderRadius: BorderRadius.circular(22),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.72),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: CSAppColors.primary.withValues(alpha: 0.75),
                          width: 1.2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: CSAppColors.primary.withValues(alpha: 0.2),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ],
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.meeting_room_outlined,
                              color: CSAppColors.primary, size: 16),
                          const SizedBox(width: 6),
                          Flexible(
                            child: Text(
                              _getHeaderTitle(),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Icon(Icons.arrow_drop_down,
                              color: Colors.white70, size: 20),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.55),
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    padding: EdgeInsets.zero,
                    icon: const Icon(Icons.flash_on,
                        color: Colors.white, size: 20),
                    onPressed: _toggleFlash,
                  ),
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
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 36),
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
                  const SizedBox(height: 14),
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
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => CSScanHistoryScreen(
                              roomId: _activeRoomId,
                              showId: _isAutoMode ? '' : _activeShowId,
                            ),
                          ),
                        );
                        if (mounted) setState(() {});
                      },
                      icon: const Icon(Icons.history, size: 18),
                      label: const Text('Lịch sử quét vé'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white24),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
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
