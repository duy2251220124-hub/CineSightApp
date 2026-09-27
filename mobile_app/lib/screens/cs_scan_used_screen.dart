

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../widgets/cs_scan_result_view.dart';



class CSScanUsedScreen extends StatelessWidget {

  final VoidCallback? onScanNext;



  const CSScanUsedScreen({

    super.key,

    this.onScanNext,

  });



  @override

  Widget build(BuildContext context) {

    return CSScanResultView(

      result: CSMockData.scanUsed,

      movie: CSMockData.movies.first,

      onScanNext: onScanNext,

    );

  }

}

