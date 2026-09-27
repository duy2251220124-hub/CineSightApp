

import 'package:flutter/material.dart';

import '../mock/mock_data.dart';

import '../widgets/cs_scan_result_view.dart';



class CSScanSuccessScreen extends StatelessWidget {

  final VoidCallback? onScanNext;



  const CSScanSuccessScreen({

    super.key,

    this.onScanNext,

  });



  @override

  Widget build(BuildContext context) {

    return CSScanResultView(

      result: CSMockData.scanSuccess,

      movie: CSMockData.movies.first,

      onScanNext: onScanNext,

    );

  }

}

