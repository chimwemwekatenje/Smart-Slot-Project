// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smartslot_android_app/main.dart';

void main() {
  testWidgets('SmartSlot app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const SmartSlotApp());

    // Verify that the app starts (splash screen or login screen should appear)
    await tester.pumpAndSettle();
    
    // The test passes if the app builds without errors
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
