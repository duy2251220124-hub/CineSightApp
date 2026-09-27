

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';



class CSSeatMap extends StatelessWidget {

  final bool showWarnings;

  final bool selectionMode;



  const CSSeatMap({

    super.key,

    this.showWarnings = false,

    this.selectionMode = false,

  });



  Color _seatColor(String seat) {

    if (selectionMode &&

        CSMockData.selectedBrokenSeats.contains(seat)) {

      return CSAppColors.danger;

    }



    if (showWarnings && CSMockData.warningSeats.contains(seat)) {

      return CSAppColors.danger;

    }



    if (CSMockData.brokenSeats.contains(seat)) {

      return CSAppColors.warning;

    }



    if (CSMockData.occupiedSeats.contains(seat)) {

      return CSAppColors.primary;

    }



    return CSAppColors.surfaceStrong;

  }



  @override

  Widget build(BuildContext context) {

    const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K'];



    return Column(

      children: [

        Container(

          width: 220,

          height: 12,

          decoration: BoxDecoration(

            border: const Border(

              top: BorderSide(

                color: CSAppColors.primary,

                width: 2,

              ),

            ),

            borderRadius: BorderRadius.circular(50),

          ),

        ),

        const Text(

          'MÀN HÌNH / SCREEN',

          style: TextStyle(

            color: CSAppColors.muted,

            fontSize: 8,

          ),

        ),

        const SizedBox(height: 14),

        ...rows.map((row) {

          return Padding(

            padding: const EdgeInsets.symmetric(vertical: 2),

            child: Row(

              mainAxisAlignment: MainAxisAlignment.center,

              children: [

                SizedBox(

                  width: 14,

                  child: Text(

                    row,

                    style: const TextStyle(

                      color: CSAppColors.muted,

                      fontSize: 9,

                    ),

                  ),

                ),

                ...List.generate(8, (index) {

                  final seat = '$row${index + 1}';



                  return Container(

                    width: 27,

                    height: 22,

                    margin: const EdgeInsets.symmetric(horizontal: 2),

                    alignment: Alignment.center,

                    decoration: BoxDecoration(

                      color: _seatColor(seat),

                      borderRadius: BorderRadius.circular(3),

                      border: Border.all(color: CSAppColors.border),

                    ),

                    child: Text(

                      seat,

                      style: const TextStyle(

                        fontSize: 7,

                        fontWeight: FontWeight.w700,

                      ),

                    ),

                  );

                }),

                SizedBox(

                  width: 14,

                  child: Text(

                    row,

                    textAlign: TextAlign.end,

                    style: const TextStyle(

                      color: CSAppColors.muted,

                      fontSize: 9,

                    ),

                  ),

                ),

              ],

            ),

          );

        }),

        const SizedBox(height: 14),

        const Wrap(

          spacing: 12,

          children: [

            CSLegendItem('Trống', CSAppColors.surfaceStrong),

            CSLegendItem('Đã có người', CSAppColors.primary),

            CSLegendItem('Trục trặc', CSAppColors.warning),

            CSLegendItem('Cảnh báo', CSAppColors.danger),

          ],

        ),

      ],

    );

  }

}



class CSLegendItem extends StatelessWidget {

  final String label;

  final Color color;



  const CSLegendItem(this.label, this.color, {super.key});



  @override

  Widget build(BuildContext context) {

    return Row(

      mainAxisSize: MainAxisSize.min,

      children: [

        Container(width: 8, height: 8, color: color),

        const SizedBox(width: 4),

        Text(

          label,

          style: const TextStyle(

            color: CSAppColors.muted,

            fontSize: 8,

          ),

        ),

      ],

    );

  }

}






