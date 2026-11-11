import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
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
  XFile? _imageFile;
  Uint8List? _imageBytes;
  final ImagePicker _picker = ImagePicker();

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

  Future<void> _pickImage(ImageSource source) async {
    try {
      final picked = await _picker.pickImage(
        source: source,
        maxWidth: 1600,
        maxHeight: 1600,
        imageQuality: 85,
      );
      if (picked != null) {
        final bytes = await picked.readAsBytes();
        setState(() {
          _imageFile = picked;
          _imageBytes = bytes;
        });
      }
    } catch (e) {
      debugPrint('[IMAGE_PICKER] Lỗi chọn ảnh: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Không thể truy cập camera/thư viện: $e')),
        );
      }
    }
  }

  Future<void> _openSeatPicker() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (pickerCtx) => CSDamagedSeatScreen(
          roomId: _selectedRoomId,
          initialSeats: _seats,
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

    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

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

    if (!mounted) return;

    if (result['success'] == true) {
      final dynamic rawIncId = result['data']?['id'] ?? result['data']?['incident_id'];
      if (_imageBytes != null && rawIncId != null) {
        final int? incId = rawIncId is int ? rawIncId : int.tryParse(rawIncId.toString());
        if (incId != null) {
          await ApiClient.uploadIncidentPhoto(
            incId,
            _imageBytes,
            filename: _imageFile?.name ?? 'incident_.jpg',
          );
        }
      }

      if (!mounted) return;
      setState(() => _isLoading = false);
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Đã tạo sự cố & lưu hiện trường thành công!'),
          backgroundColor: CSAppColors.success,
        ),
      );
      if (widget.onIncidentAdded != null) {
        widget.onIncidentAdded!();
      } else {
        navigator.pop(true);
      }
    } else {
      setState(() => _isLoading = false);
      messenger.showSnackBar(
        SnackBar(content: Text(result['error'] ?? 'Lỗi không xác định')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Scaffold(
          backgroundColor: CSAppColors.background,
          body: SafeArea(
            bottom: false,
            child: Column(
              children: [
                const CSScreenHeader(
                  title: 'Báo cáo sự cố mới',
                  subtitle: 'Ghi nhận & bàn giao ca kỹ thuật',
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(10, 0, 10, 125),
                    children: [
                      const CSFormLabel('LOẠI SỰ CỐ'),
                      DropdownButtonFormField<String>(
                        initialValue: _category,
                        dropdownColor: CSAppColors.surface,
                        style: TextStyle(color: CSAppColors.textPrimary, fontSize: 13.5),
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
                        dropdownColor: CSAppColors.surface,
                        style: TextStyle(color: CSAppColors.textPrimary, fontSize: 13.5),
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
                                  border: Border.all(color: CSAppColors.border),
                                ),
                                child: Text(
                                  _seats.isNotEmpty
                                      ? _seats.join(', ')
                                      : 'Chưa chọn ghế nào',
                                  style: TextStyle(
                                    color: _seats.isNotEmpty ? CSAppColors.textPrimary : CSAppColors.muted,
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
                        style: TextStyle(color: CSAppColors.textPrimary),
                        decoration: const InputDecoration(hintText: 'Nhập tiêu đề (bắt buộc)'),
                      ),
                      const SizedBox(height: 12),
                      const CSFormLabel('MÔ TẢ CHI TIẾT SỰ CỐ'),
                      TextFormField(
                        controller: _descController,
                        maxLines: 4,
                        style: TextStyle(color: CSAppColors.textPrimary),
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
                                  side: BorderSide(
                                    color: selected
                                        ? CSAppColors.danger
                                        : CSAppColors.border,
                                  ),
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
                      const CSFormLabel('ẢNH CHỤP HIỆN TRƯỜNG / THỰC TẾ'),
                      if (_imageFile == null)
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () => _pickImage(ImageSource.camera),
                                icon: const Icon(Icons.camera_alt_outlined, size: 16),
                                label: const Text('Chụp ảnh thực tế', style: TextStyle(fontSize: 12)),
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: () => _pickImage(ImageSource.gallery),
                                icon: const Icon(Icons.photo_library_outlined, size: 16),
                                label: const Text('Chọn từ máy', style: TextStyle(fontSize: 12)),
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                ),
                              ),
                            ),
                          ],
                        )
                      else
                        Container(
                          decoration: BoxDecoration(
                            color: CSAppColors.surfaceStrong,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: CSAppColors.border),
                          ),
                          padding: const EdgeInsets.all(8),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Stack(
                                alignment: Alignment.topRight,
                                children: [
                                  ClipRRect(
                                    borderRadius: BorderRadius.circular(8),
                                    child: Image.memory(
                                      _imageBytes!,
                                      height: 180,
                                      width: double.infinity,
                                      fit: BoxFit.cover,
                                    ),
                                  ),
                                  IconButton(
                                    tooltip: 'Xóa ảnh',
                                    style: IconButton.styleFrom(
                                      backgroundColor: Colors.black87,
                                      foregroundColor: Colors.white,
                                    ),
                                    icon: const Icon(Icons.close, size: 18),
                                    onPressed: () => setState(() {
                                      _imageFile = null;
                                      _imageBytes = null;
                                    }),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Expanded(
                                    child: Text(
                                      'Ảnh: ${_imageFile!.path.split(RegExp(r"[/\\]")).last}',
                                      style: TextStyle(color: CSAppColors.muted, fontSize: 11),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  TextButton.icon(
                                    onPressed: () => _pickImage(ImageSource.camera),
                                    icon: const Icon(Icons.refresh, size: 14),
                                    label: const Text('Đổi ảnh', style: TextStyle(fontSize: 11)),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 18),
                      CSPrimaryButton(
                        label: 'Tạo sự cố & bàn giao ca',
                        onPressed: _submit,
                      ),
                    ],
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
        style: TextStyle(
          color: CSAppColors.muted,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
