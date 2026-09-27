

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';



class CSPrimaryButton extends StatelessWidget {

  final String label;

  final VoidCallback? onPressed;

  final Color color;

  final IconData? icon;



  const CSPrimaryButton({

    super.key,

    required this.label,

    this.onPressed,

    this.color = CSAppColors.primary,

    this.icon,

  });



  @override

  Widget build(BuildContext context) {

    return SizedBox(

      width: double.infinity,

      height: 48,

      child: FilledButton(

        onPressed: onPressed,

        style: FilledButton.styleFrom(

          backgroundColor: color,

          shape: RoundedRectangleBorder(

            borderRadius: BorderRadius.circular(9),

          ),

        ),

        child: Row(

          mainAxisAlignment: MainAxisAlignment.center,

          children: [

            if (icon != null) ...[

              Icon(icon, size: 18),

              const SizedBox(width: 8),

            ],

            Text(

              label,

              style: const TextStyle(fontWeight: FontWeight.w700),

            ),

          ],

        ),

      ),

    );

  }

}




