

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../theme/app_theme.dart';

import '../widgets/cs_app_card.dart';



class CSScanScreen extends StatelessWidget {

  final VoidCallback? onBack;

  final VoidCallback? onToggleFlash;

  final VoidCallback? onLookup;



  const CSScanScreen({

    super.key,

    this.onBack,

    this.onToggleFlash,

    this.onLookup,

  });



  @override

  Widget build(BuildContext context) {

    final result = CSMockData.scanSuccess;



    return Scaffold(

      body: SafeArea(

        child: Stack(

          children: [

            Positioned(

              top: 4,

              left: 8,

              child: IconButton(

                onPressed: onBack ?? () => Navigator.maybePop(context),

                icon: const Icon(Icons.chevron_left),

              ),

            ),

            Positioned(

              top: 4,

              right: 8,

              child: IconButton(

                onPressed: onToggleFlash,

                icon: const Icon(Icons.flashlight_on_outlined),

              ),

            ),

            Center(

              child: Transform.translate(

                offset: const Offset(0, -65),

                child: Container(

                  width: 290,

                  height: 290,

                  decoration: BoxDecoration(

                    border: Border.all(

                      color: CSAppColors.primary,

                      width: 3,

                    ),

                    borderRadius: BorderRadius.circular(20),

                  ),

                ),

              ),

            ),

            Positioned(

              left: 16,

              right: 16,

              bottom: 18,

              child: CSAppCard(

                child: Column(

                  children: [

                    const Text(

                      'Đưa mã QR vào khung hình',

                      style: TextStyle(color: CSAppColors.muted),

                    ),

                    const SizedBox(height: 12),

                    Row(

                      children: [

                        Expanded(

                          child: CSScanStat(

                            value: '${result.scanned}',

                            label: 'Đã soát',

                            color: CSAppColors.success,

                          ),

                        ),

                        const SizedBox(width: 10),

                        Expanded(

                          child: CSScanStat(

                            value: '${result.total}',

                            label: 'Tổng vé',

                            color: Colors.white,

                          ),

                        ),

                      ],

                    ),

                    const SizedBox(height: 10),

                    Row(

                      children: [

                        Expanded(

                          child: OutlinedButton.icon(

                            onPressed: onToggleFlash,

                            icon: const Icon(Icons.flashlight_on_outlined),

                            label: const Text('Bật đèn'),

                          ),

                        ),

                        const SizedBox(width: 10),

                        Expanded(

                          child: OutlinedButton.icon(

                            onPressed: onLookup,

                            icon: const Icon(Icons.search),

                            label: const Text('Tra cứu'),

                          ),

                        ),

                      ],

                    ),

                  ],

                ),

              ),

            ),

          ],

        ),

      ),

    );

  }

}



class CSScanStat extends StatelessWidget {

  final String value;

  final String label;

  final Color color;



  const CSScanStat({

    super.key,

    required this.value,

    required this.label,

    required this.color,

  });



  @override

  Widget build(BuildContext context) {

    return Container(

      padding: const EdgeInsets.all(10),

      decoration: BoxDecoration(

        color: CSAppColors.surfaceStrong,

        borderRadius: BorderRadius.circular(8),

      ),

      child: Column(

        children: [

          Text(

            value,

            style: TextStyle(

              color: color,

              fontSize: 18,

              fontWeight: FontWeight.w800,

            ),

          ),

          Text(

            label,

            style: const TextStyle(

              color: CSAppColors.muted,

              fontSize: 10,

            ),

          ),

        ],

      ),

    );

  }

}

