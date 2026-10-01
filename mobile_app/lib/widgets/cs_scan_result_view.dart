

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import 'cs_app_card.dart';

import 'cs_primary_button.dart';



class CSScanResultView extends StatelessWidget {

  final CSMockScanResult result;

  final CSMockMovie movie;

  final VoidCallback? onScanNext;



  const CSScanResultView({

    super.key,

    required this.result,

    required this.movie,

    this.onScanNext,

  });



  Color get _color {

    return switch (result.type) {

      CSScanResultType.success => CSAppColors.primary,

      CSScanResultType.wait => CSAppColors.warning,

      CSScanResultType.used => CSAppColors.danger,

    };

  }



  IconData get _icon {

    return switch (result.type) {

      CSScanResultType.success => Icons.check,

      CSScanResultType.wait => Icons.priority_high,

      CSScanResultType.used => Icons.error_outline,

    };

  }



  @override

  Widget build(BuildContext context) {

        return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: CSAppColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: SafeArea(

        child: Column(

          children: [

            Container(

              width: double.infinity,

              padding: const EdgeInsets.symmetric(vertical: 22),

              decoration: BoxDecoration(border: Border.all(color: _color), borderRadius: const BorderRadius.vertical(top: Radius.circular(20))),

              child: Column(

                children: [

                  CircleAvatar(

                    radius: 27,

                    backgroundColor: _color,

                    child: Icon(_icon, color: Colors.white),

                  ),

                  const SizedBox(height: 12),

                  Text(

                    result.title,

                    style: const TextStyle(

                      fontSize: 18,

                      fontWeight: FontWeight.w800,

                    ),

                  ),

                ],

              ),

            ),

            Expanded(

              child: ListView(

                padding: const EdgeInsets.all(14),

                children: [

                  CSAppCard(

                    child: Column(

                      crossAxisAlignment: CrossAxisAlignment.start,

                      children: [

                        Text(

                          movie.title,

                          style: const TextStyle(

                            fontWeight: FontWeight.w700,

                          ),

                        ),

                        const SizedBox(height: 5),

                        Text(

                          '${movie.time} | ${movie.room}',

                          style: const TextStyle(

                            color: CSAppColors.muted,

                            fontSize: 11,

                          ),

                        ),

                      ],

                    ),

                  ),

                  const SizedBox(height: 10),

                  Row(

                    children: [

                      Expanded(

                        child: CSAppCard(

                          child: Column(

                            crossAxisAlignment: CrossAxisAlignment.start,

                            children: [

                              const Text(

                                'Ghế',

                                style: TextStyle(

                                  color: CSAppColors.muted,

                                ),

                              ),

                              Text(

                                result.seat,

                                style: TextStyle(

                                  color: _color,

                                  fontSize: 19,

                                  fontWeight: FontWeight.w800,

                                ),

                              ),

                            ],

                          ),

                        ),

                      ),

                      const SizedBox(width: 10),

                      Expanded(

                        child: CSAppCard(

                          child: Column(

                            crossAxisAlignment: CrossAxisAlignment.start,

                            children: [

                              const Text(

                                'Số lượng',

                                style: TextStyle(

                                  color: CSAppColors.muted,

                                ),

                              ),

                              Text(

                                result.quantity,

                                style: const TextStyle(

                                  fontSize: 18,

                                  fontWeight: FontWeight.w800,

                                ),

                              ),

                            ],

                          ),

                        ),

                      ),

                    ],

                  ),

                  const SizedBox(height: 10),

                  CSAppCard(

                    child: result.type == CSScanResultType.success

                        ? Column(

                            children: [

                              CSScanInfoRow(

                                label: 'Khách hàng',

                                value: result.customer,

                              ),

                              const SizedBox(height: 10),

                              CSScanInfoRow(

                                label: 'Mã vé',

                                value: result.ticketCode,

                              ),

                            ],

                          )

                        : Column(

                            children: [

                              CSScanInfoRow(

                                label: 'Vé đã sử dụng lúc',

                                value: result.usedAt,

                              ),

                              const SizedBox(height: 10),

                              CSScanInfoRow(

                                label: 'Địa điểm quét trước',

                                value: result.previousGate,

                              ),

                            ],

                          ),

                  ),

                  if (result.type != CSScanResultType.used) ...[

                    const SizedBox(height: 12),

                    Container(

                      height: 40,

                      alignment: Alignment.center,

                      decoration: BoxDecoration(

                        border: Border.all(color: _color),

                        borderRadius: BorderRadius.circular(8),

                      ),

                      child: Text(

                        result.type == CSScanResultType.success

                            ? 'Được phép vào rạp'

                            : 'Vui lòng đợi thêm 5 phút',

                        style: TextStyle(

                          color: _color,

                          fontWeight: FontWeight.w700,

                        ),

                      ),

                    ),

                  ],

                ],

              ),

            ),

            Padding(

              padding: const EdgeInsets.all(14),

              child: Row(

                children: [

                  Expanded(

                    child: Text(

                      'Đã soát\n${result.scanned} / ${result.total}',

                      style: const TextStyle(fontWeight: FontWeight.w700),

                    ),

                  ),

                  Expanded(

                    flex: 3,

                    child: CSPrimaryButton(

                      label: 'Quét tiếp',

                      color: _color,

                      onPressed: onScanNext,

                    ),

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



class CSScanInfoRow extends StatelessWidget {

  final String label;

  final String value;



  const CSScanInfoRow({

    super.key,

    required this.label,

    required this.value,

  });



  @override

  Widget build(BuildContext context) {

    return Row(

      children: [

        Expanded(

          child: Text(

            label,

            style: const TextStyle(color: CSAppColors.muted),

          ),

        ),

        Text(

          value,

          style: const TextStyle(

            color: CSAppColors.primary,

            fontWeight: FontWeight.w700,

          ),

        ),

      ],

    );

  }

}

