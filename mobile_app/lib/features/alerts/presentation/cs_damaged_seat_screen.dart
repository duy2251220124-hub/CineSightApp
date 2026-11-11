import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/utils/room_utils.dart';
import 'package:mobile_app/core/widgets/cs_app_card.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/features/rooms/presentation/widgets/cs_seat_map.dart';

class CSDamagedSeatScreen extends StatefulWidget {
  final String roomId;
  final List<String> initialSeats;
  final ValueChanged<List<String>>? onAddPhoto;

  const CSDamagedSeatScreen({
    super.key,
    this.roomId = 'room1',
    this.initialSeats = const [],
    this.onAddPhoto,
  });

  @override
  State<CSDamagedSeatScreen> createState() => _CSDamagedSeatScreenState();
}

class _CSDamagedSeatScreenState extends State<CSDamagedSeatScreen> {
  late final Set<String> _selectedSeats;

  @override
  void initState() {
    super.initState();
    _selectedSeats = Set<String>.from(widget.initialSeats);
  }

  @override
  Widget build(BuildContext context) {
    final seats = _selectedSeats.toList()..sort();
    final hasSeats = seats.isNotEmpty;
    final roomDisplay = formatRoomName(widget.roomId);

    return Scaffold(
      backgroundColor: CSAppColors.background,
      body: SafeArea(
        bottom: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
          child: Column(
            children: [
              CSScreenHeader(
                title: 'Báo ghế hư - $roomDisplay',
                subtitle: 'Chạm vào ghế trên sơ đồ để chọn hoặc bỏ chọn',
              ),
              // Ghi chú màu ghế căn giữa
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                alignment: Alignment.center,
                child: Wrap(
                  alignment: WrapAlignment.center,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: 20,
                  runSpacing: 8,
                  children: [
                    CSLegendItem('Ghế bình thường', CSAppColors.seatEmpty),
                    const CSLegendItem('Đang chọn báo hỏng', CSAppColors.warning),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              CSAppCard(
                child: CSSeatMap(
                  roomId: widget.roomId,
                  selectionMode: true,
                  selectedSeats: _selectedSeats,
                  onSeatTapped: (seat) {
                    setState(() {
                      if (_selectedSeats.contains(seat)) {
                        _selectedSeats.remove(seat);
                      } else {
                        _selectedSeats.add(seat);
                      }
                    });
                  },
                ),
              ),
              const SizedBox(height: 12),
              CSAppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            hasSeats
                                ? 'Ghế đã chọn (${seats.length})'
                                : 'Chưa chọn ghế nào',
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              color: CSAppColors.textPrimary,
                            ),
                          ),
                        ),
                        if (hasSeats)
                          TextButton(
                            onPressed: () => setState(() => _selectedSeats.clear()),
                            child: const Text('Bỏ chọn tất cả'),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    if (hasSeats)
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: seats
                            .map(
                              (seat) => InputChip(
                                label: Text(seat),
                                labelStyle: TextStyle(
                                  color: CSAppColors.textPrimary,
                                  fontWeight: FontWeight.w700,
                                ),
                                backgroundColor: CSAppColors.warning.withValues(alpha: 0.2),
                                side: const BorderSide(
                                  color: CSAppColors.warning,
                                ),
                                deleteIconColor: CSAppColors.textPrimary,
                                onDeleted: () => setState(() => _selectedSeats.remove(seat)),
                              ),
                            )
                            .toList(),
                      )
                    else
                      Text(
                        'Chạm vào ghế bị hỏng trên sơ đồ, ghế sẽ chuyển sang màu cam.',
                        style: TextStyle(
                          color: CSAppColors.muted,
                          fontSize: 11.5,
                        ),
                      ),
                    const SizedBox(height: 12),
                    CSPrimaryButton(
                      label: 'Xác nhận ghế hư (${seats.length})',
                      icon: Icons.check_circle_outline,
                      onPressed: hasSeats && widget.onAddPhoto != null
                          ? () => widget.onAddPhoto!(seats)
                          : null,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
