

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_primary_button.dart';

import '../widgets/cs_screen_header.dart';



class CSAddIncidentScreen extends StatefulWidget {

  final VoidCallback? onSubmit;

  final VoidCallback? onAddPhoto;



  const CSAddIncidentScreen({

    super.key,

    this.onSubmit,

    this.onAddPhoto,

  });



  @override

  State<CSAddIncidentScreen> createState() =>

      _CSAddIncidentScreenState();

}



class _CSAddIncidentScreenState extends State<CSAddIncidentScreen> {

  int _severity = 2;



  @override

  Widget build(BuildContext context) {

    final incident = CSMockData.incidents[1];



    return Scaffold(

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

                  const CSFormLabel('CHỌN PHÒNG / RẠP CHIẾU'),

                  DropdownButtonFormField<String>(

                    initialValue: incident.room,

                    items: CSMockData.rooms.map((room) {

                      return DropdownMenuItem(

                        value: room.name,

                        child: Text(room.name),

                      );

                    }).toList(),

                    onChanged: (_) {},

                  ),

                  const SizedBox(height: 12),

                  const CSFormLabel('VỊ TRÍ / HẠNG MỤC SỰ CỐ'),

                  TextFormField(

                    initialValue: incident.position,

                  ),

                  const SizedBox(height: 12),

                  const CSFormLabel('TIÊU ĐỀ SỰ CỐ'),

                  TextFormField(

                    initialValue: incident.title,

                  ),

                  const SizedBox(height: 12),

                  const CSFormLabel('MÔ TẢ CHI TIẾT SỰ CỐ'),

                  TextFormField(

                    initialValue: incident.description,

                    maxLines: 4,

                  ),

                  const SizedBox(height: 12),

                  const CSFormLabel('MỨC ĐỘ ƯU TIÊN KHẮC PHỤC'),

                  Row(

                    children: List.generate(3, (index) {

                      const labels = [

                        'Thấp',

                        'Trung bình',

                        'Cao (Khẩn cấp)',

                      ];

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

                      onTap: widget.onAddPhoto,

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

                onPressed: widget.onSubmit,

              ),

            ),

          ],

        ),

      ),

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

