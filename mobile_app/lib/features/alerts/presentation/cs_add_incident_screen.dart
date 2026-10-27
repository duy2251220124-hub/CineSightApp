import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';
import 'package:mobile_app/core/network/api_client.dart';
import 'package:mobile_app/features/alerts/presentation/cs_damaged_seat_screen.dart';

class CSAddIncidentScreen extends StatefulWidget {
  final List<String> reportedSeats;
  final String? roomId;
  final String? showId;
  final String? initialCategory;
  final VoidCallback? onIncidentAdded;

  const CSAddIncidentScreen({
    super.key,
    required this.reportedSeats,
    this.roomId,
    this.showId,
    this.initialCategory,
    this.onIncidentAdded,
  });

  @override
  State<CSAddIncidentScreen> createState() => _CSAddIncidentScreenState();
}

class _CSAddIncidentScreenState extends State<CSAddIncidentScreen> {
  int _severity = 2; // Mặc định: 'Cao (Khẩn cấp)' -> 'high'
  String _category = 'seat_damage';
  String _selectedRoomId = 'room1';
  late List<String> _seats;
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialCategory != null) {
      _category = widget.initialCategory!;
    }
    if (widget.roomId != null && widget.roomId!.isNotEmpty) {
      _selectedRoomId = widget.roomId!.replaceAll('seats_config_', '').trim();
    }
    _seats = List<String>.from(widget.reportedSeats);

    if (_seats.isNotEmpty) {
      _titleController.text = 'Hỏng ghế ${_seats.join(', ')}';
      _descController.text = 'Cần kiểm tra và sửa chữa ghế ${_seats.join(', ')}';
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    super.dispose();
  }

  Future<void> _openSeatPicker() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (pickerCtx) => CSDamagedSeatScreen(
          onAddPhoto: (pickedSeats) {
            setState(() {
              _seats = List<String>.from(pickedSeats);
              if (_seats.isNotEmpty && _titleController.text.trim().isEmpty) {
                _titleController.text = 'Hỏng ghế ${_seats.join(', ')}';
              }
              if (_seats.isNotEmpty && _descController.text.trim().isEmpty) {
                _descController.text = 'Cần kiểm tra và sửa chữa ghế ${_seats.join(', ')}';
              }
            });
            Navigator.pop(pickerCtx);
          },
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (_titleController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng nhập tiêu đề sự cố')),
      );
      return;
    }

    setState(() => _isLoading = true);

    String severityStr = 'low';
    if (_severity == 1) severityStr = 'medium';
    if (_severity == 2) severityStr = 'high';

    final result = await ApiClient.createIncident(
      category: _category,
      severity: severityStr,
      title: _titleController.text.trim(),
      description: _descController.text.trim(),
      roomId: _selectedRoomId,
      showId: (widget.showId != null &&
              widget.showId!.isNotEmpty &&
              widget.showId != 'auto' &&
              widget.showId != 'all')
          ? widget.showId
          : null,
      seatIds: _seats,
    );

    if (mounted) {
      setState(() => _isLoading = false);

      if (result['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã tạo sự cố thành công')),
        );
        if (widget.onIncidentAdded != null) {
          widget.onIncidentAdded!();
        } else {
          Navigator.of(context).pop(true);
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['error'] ?? 'Lỗi không xác định')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Scaffold(
          body: SafeArea(
            child: Column(
              children: [
                const CSScreenHeader(
                  title: 'Báo cáo sự cố mới',
                  subtitle: 'Ghi nhận & bàn giao ca kỹ thuật',
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    children: [
                      const CSFormLabel('LOẠI SỰ CỐ'),
                      DropdownButtonFormField<String>(
                        initialValue: _category,
                        items: const [
                          DropdownMenuItem(value: 'seat_damage', child: Text('Ghế hỏng')),
                          DropdownMenuItem(value: 'equipment', child: Text('Lỗi thiết bị (máy chiếu, âm thanh...)')),
                          DropdownMenuItem(value: 'facility', child: Text('Vệ sinh/Cơ sở vật chất')),
                          DropdownMenuItem(value: 'other', child: Text('Khác')),
                        ],
                        onChanged: (val) {
                          if (val != null) setState(() => _category = val);
                        },
                      ),
                      const SizedBox(height: 12),
                      const CSFormLabel('PHÒNG / RẠP CHIẾU'),
                      DropdownButtonFormField<String>(
                        initialValue: _selectedRoomId,
                        items: const [
                          DropdownMenuItem(value: 'room1', child: Text('Phòng chiếu số 1')),
                          DropdownMenuItem(value: 'room2', child: Text('Phòng chiếu số 2')),
                          DropdownMenuItem(value: 'room3', child: Text('Phòng chiếu số 3')),
                          DropdownMenuItem(value: 'room4', child: Text('Phòng chiếu số 4')),
                        ],
                        onChanged: (val) {
                          if (val != null) setState(() => _selectedRoomId = val);
                        },
                      ),
                      const SizedBox(height: 12),
                      if (_category == 'seat_damage' || _seats.isNotEmpty) ...[
                        const CSFormLabel('VỊ TRÍ GHẾ HỎNG'),
                        Row(
                          children: [
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                                decoration: BoxDecoration(
                                  color: CSAppColors.surfaceStrong,
                                  borderRadius: BorderRadius.circular(9),
                                ),
                                child: Text(
                                  _seats.isNotEmpty
                                      ? _seats.join(', ')
                                      : 'Chưa chọn ghế nào',
                                  style: TextStyle(
                                    color: _seats.isNotEmpty ? Colors.white : CSAppColors.muted,
                                    fontWeight: _seats.isNotEmpty ? FontWeight.w600 : FontWeight.normal,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            OutlinedButton.icon(
                              onPressed: _openSeatPicker,
                              icon: const Icon(Icons.grid_on_outlined, size: 16),
                              label: const Text('Chọn trên sơ đồ'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                      ],
                      const CSFormLabel('TIÊU ĐỀ SỰ CỐ'),
                      TextFormField(
                        controller: _titleController,
                        decoration: const InputDecoration(hintText: 'Nhập tiêu đề (bắt buộc)'),
                      ),
                      const SizedBox(height: 12),
                      const CSFormLabel('MÔ TẢ CHI TIẾT SỰ CỐ'),
                      TextFormField(
                        controller: _descController,
                        maxLines: 4,
                        decoration: const InputDecoration(hintText: 'Nhập mô tả chi tiết'),
                      ),
                      const SizedBox(height: 12),
                      const CSFormLabel('MỨC ĐỘ ƯU TIÊN KHẮC PHỤC'),
                      Row(
                        children: List.generate(3, (index) {
                          const labels = ['Thấp', 'Trung bình', 'Cao (Khẩn cấp)'];
                          final selected = _severity == index;

                          return Expanded(
                            child: Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: OutlinedButton(
                                onPressed: () {
                                  setState(() => _severity = index);
                                },
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: selected
                                      ? CSAppColors.danger
                                      : CSAppColors.muted,
                                ),
                                child: Text(
                                  labels[index],
                                  style: const TextStyle(fontSize: 10),
                                ),
                              ),
                            ),
                          );
                        }),
                      ),
                      const SizedBox(height: 12),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(10),
                  child: CSPrimaryButton(
                    label: 'Tạo sự cố & bàn giao ca',
                    onPressed: _submit,
                  ),
                ),
              ],
            ),
          ),
        ),
        if (_isLoading)
          Container(
            color: Colors.black54,
            child: const Center(
              child: CircularProgressIndicator(),
            ),
          ),
      ],
    );
  }
}

class CSFormLabel extends StatelessWidget {
  final String text;

  const CSFormLabel(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: const TextStyle(
          color: CSAppColors.muted,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
