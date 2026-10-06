import sys
import re

with open(r'c:\CineSightApp\mobile_app\lib\features\scanner\presentation\scanner_screen.dart', 'r', encoding='utf-8') as f:
    content = f.read()

# Add _simulateScan logic
simulate_method = '''
  void _simulateScan(String payload) {
    if (isProcessing) return;
    setState(() => isProcessing = true);
    
    // Fake BarcodeCapture
    final mockBarcode = Barcode(rawValue: payload, format: BarcodeFormat.qrCode);
    final mockCapture = BarcodeCapture(barcodes: [mockBarcode]);
    
    // We delay slightly to simulate processing, then handle normally.
    // However, _handleBarcode is private and takes a BarcodeCapture.
    // Actually, we can just call _handleBarcode(mockCapture) but wait, we need to bypass isProcessing check there or just reset it.
    setState(() => isProcessing = false); 
    _handleBarcode(mockCapture);
  }
'''

content = content.replace('  void _handleBarcode(BarcodeCapture capture) async {', simulate_method + '\n  void _handleBarcode(BarcodeCapture capture) async {')

# Add debug button in build
debug_buttons = '''
            if (isProcessing)
              const Center(
                child: CircularProgressIndicator(),
              ),
            // DEBUG BUTTONS
            if (kDebugMode)
              Positioned(
                right: 10,
                bottom: 150,
                child: Column(
                  children: [
                    FloatingActionButton(
                      heroTag: 'test_btn_1',
                      onPressed: () => _simulateScan('{"v":1,"ticket":"TICK-999","room":"room1","seat":"C05","show":"2026-10-05T19:30"}'),
                      child: const Icon(Icons.qr_code_2),
                    ),
                  ],
                ),
              ),
'''

content = content.replace('''            if (isProcessing)
              const Center(
                child: CircularProgressIndicator(),
              ),''', debug_buttons)

# Add foundation import if missing
if 'import \'package:flutter/foundation.dart\';' not in content:
    content = content.replace('import \'package:flutter/material.dart\';', 'import \'package:flutter/material.dart\';\nimport \'package:flutter/foundation.dart\';')

with open(r'c:\CineSightApp\mobile_app\lib\features\scanner\presentation\scanner_screen.dart', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched successfully!')
