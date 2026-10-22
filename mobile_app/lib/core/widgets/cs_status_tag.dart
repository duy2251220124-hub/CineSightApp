

import 'package:flutter/material.dart';



class CSStatusTag extends StatelessWidget {

  final String text;

  final Color color;



  const CSStatusTag({

    super.key,

    required this.text,

    required this.color,

  });



  @override

  Widget build(BuildContext context) {

    return Container(

      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),

      decoration: BoxDecoration(

        color: color.withValues(alpha: .14),

        borderRadius: BorderRadius.circular(4),

      ),

      child: Text(

        text,

        style: TextStyle(

          color: color,

          fontSize: 10,

          fontWeight: FontWeight.w700,

        ),

      ),

    );

  }

}




