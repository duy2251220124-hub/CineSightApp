

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';



class CSBottomNav extends StatelessWidget {

  final int selectedIndex;

  final ValueChanged<int>? onChanged;



  const CSBottomNav({

    super.key,

    required this.selectedIndex,

    this.onChanged,

  });



  @override

  Widget build(BuildContext context) {

    const items = [

      (Icons.home_outlined, 'Trang chủ'),

      (Icons.confirmation_number_outlined, 'Quét vé'),

      (Icons.notifications_none, 'Cảnh báo'),

      (Icons.settings_outlined, 'Cài đặt'),

    ];



    return Container(

      height: 80,

      decoration: const BoxDecoration(

        color: CSAppColors.surface,

        border: Border(

          top: BorderSide(color: CSAppColors.border),

        ),

      ),

      child: Row(

        children: List.generate(items.length, (index) {

          final selected = selectedIndex == index;

          final item = items[index];



          return Expanded(

            child: InkWell(

              onTap: () => onChanged?.call(index),

              child: Column(

                mainAxisAlignment: MainAxisAlignment.center,

                children: [

                  Icon(

                    item.$1,

                    color: selected

                        ? CSAppColors.primary

                        : CSAppColors.muted,

                  ),

                  const SizedBox(height: 5),

                  Text(

                    item.$2,

                    style: TextStyle(

                      fontSize: 11,

                      color: selected

                          ? CSAppColors.primary

                          : CSAppColors.muted,

                    ),

                  ),

                ],

              ),

            ),

          );

        }),

      ),

    );

  }

}




