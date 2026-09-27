

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';



class CSAppCard extends StatelessWidget {

  final Widget child;

  final EdgeInsetsGeometry padding;

  final Color? color;

  final Color? borderColor;

  final VoidCallback? onTap;



  const CSAppCard({

    super.key,

    required this.child,

    this.padding = const EdgeInsets.all(14),

    this.color,

    this.borderColor,

    this.onTap,

  });



  @override

  Widget build(BuildContext context) {

    final content = Container(

      width: double.infinity,

      padding: padding,

      decoration: BoxDecoration(

        color: color ?? CSAppColors.surface,

        borderRadius: BorderRadius.circular(10),

        border: Border.all(

          color: borderColor ?? CSAppColors.border,

        ),

      ),

      child: child,

    );



    if (onTap == null) return content;



    return InkWell(

      borderRadius: BorderRadius.circular(10),

      onTap: onTap,

      child: content,

    );

  }

}






