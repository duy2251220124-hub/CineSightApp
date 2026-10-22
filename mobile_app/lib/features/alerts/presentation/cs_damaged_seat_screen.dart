import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/features/rooms/presentation/widgets/cs_seat_map.dart';

class CSDamagedSeatScreen extends StatefulWidget {
  final ValueChanged<List<String>>? onAddPhoto;

  const CSDamagedSeatScreen({super.key, this.onAddPhoto});

  @override
  State<CSDamagedSeatScreen> createState() => _CSDamagedSeatScreenState();
}

class _CSDamagedSeatScreenState extends State<CSDamagedSeatScreen> {
  final Set<String> _selectedSeats = {};

  @override
  Widget build(BuildContext context) {
    final seats = _selectedSeats.toList();
    seats.sort();
    final hasSeats = seats.isNotEmpty;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: Column(
                  children: [
                    const CSScreenHeader(
                      title: 'Báo ghế hư',
                      subtitle: 'Chạm vào ghế để chọn / bỏ chọn',
                    ),
                    CSSeatMap(
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
                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: const BoxDecoration(
                color: CSAppColors.surface,
                border: Border(top: BorderSide(color: CSAppColors.border)),
              ),
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
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
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
                              labelStyle: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                              ),
                              backgroundColor: CSAppColors.warning.withValues(alpha: 0.25),
                              side: const BorderSide(
                                color: CSAppColors.warning,
                              ),
                              deleteIconColor: Colors.white,
                              onDeleted: () => setState(() => _selectedSeats.remove(seat)),
                            ),
                          )
                          .toList(),
                    )
                  else
                    const Text(
                      'Chạm vào ghế trên sơ đồ, ghế sẽ chuyển sang màu cam.',
                      style: TextStyle(
                        color: CSAppColors.muted,
                        fontSize: 11,
                      ),
                    ),
                  const SizedBox(height: 10),
                  CSPrimaryButton(
                    label: 'Thêm ảnh ghế hư',
                    icon: Icons.add_a_photo_outlined,
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
    );
  }
}
