import 'package:flutter/material.dart';
import 'package:mobile_app/theme/app_theme.dart';
import 'package:mobile_app/core/widgets/cs_primary_button.dart';
import 'package:mobile_app/core/widgets/cs_screen_header.dart';

import 'package:mobile_app/core/network/api_client.dart';

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
  int _severity = 2; // Default to 'Cao (Khẩn cấp)' -> map to 'high'
  String _category = 'seat_damage';
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialCategory != null) {
      _category = widget.initialCategory!;
    }
    
    if (widget.reportedSeats.isNotEmpty) {
      _titleController.text = 'Hỏng ghế ${widget.reportedSeats.join(', ')}';
      _descController.text = 'Cần kiểm tra và sửa chữa ghế ${widget.reportedSeats.join(', ')}';
    } else {
      _titleController.text = '';
      _descController.text = '';
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    super.dispose();
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
      roomId: widget.roomId,
      showId: widget.showId,
      seatIds: widget.reportedSeats,
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
          // If called from home screen flow (2 pushes), pop 2 times or to home.
          // In the new flow, we might just pop until first if not passed callback.
          Navigator.of(context).popUntil((route) => route.isFirst);
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
                        value: _category,
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
                      if (widget.roomId != null) ...[
                        const CSFormLabel('PHÒNG / RẠP CHIẾU'),
                        TextFormField(
                          initialValue: widget.roomId,
                          enabled: false,
                        ),
                        const SizedBox(height: 12),
                      ],
                      if (widget.reportedSeats.isNotEmpty) ...[
                        const CSFormLabel('VỊ TRÍ GHẾ'),
                        TextFormField(
                          initialValue: widget.reportedSeats.join(', '),
                          enabled: false,
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
                      const CSFormLabel('ẢNH CHỤP THỰC TẾ ĐÍNH KÈM'),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: InkWell(
                          onTap: () {},
                          child: Container(
                            width: 68,
                            height: 68,
                            decoration: BoxDecoration(
                              color: CSAppColors.surface,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: CSAppColors.border),
                            ),
                            child: const Icon(Icons.add_a_photo_outlined),
                          ),
                        ),
                      ),
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
