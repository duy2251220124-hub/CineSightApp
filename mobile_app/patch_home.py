import os
import re

with open('lib/features/home/presentation/home_screen.dart', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r"builder:\s*\(ctx4\)\s*=>\s*CSAddIncidentScreen\(\s*reportedSeats:\s*seats,\s*onSubmit:\s*\(\)\s*=>\s*Navigator\.of\(ctx4\)\s*\.\.pop\(\)\s*\.\.pop\(\),\s*\),",
    """builder: (ctx4) => CSAddIncidentScreen(
                                          reportedSeats: seats,
                                          onSubmit: () async {
                                            await ApiClient.createAlert(
                                              roomId: _selectedShowtime['roomId'],
                                              showId: _selectedShowtime['showId'],
                                              alertType: 'damaged_seat',
                                              seats: seats,
                                            );
                                            if (ctx4.mounted) {
                                              ScaffoldMessenger.of(ctx4).showSnackBar(
                                                const SnackBar(content: Text('Đã báo cáo sự cố thành công')),
                                              );
                                              Navigator.of(ctx4)..pop()..pop();
                                            }
                                          },
                                        ),""",
    content
)

# And make sure api_client is imported in home_screen.dart
if "import 'package:mobile_app/core/network/api_client.dart';" not in content:
    content = content.replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:mobile_app/core/network/api_client.dart';")

with open('lib/features/home/presentation/home_screen.dart', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed home_screen")
