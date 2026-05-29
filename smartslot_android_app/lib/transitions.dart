import 'package:flutter/material.dart';

class SlideUpRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  SlideUpRoute({required this.page})
      : super(
          transitionDuration: const Duration(milliseconds: 350),
          reverseTransitionDuration: const Duration(milliseconds: 280),
          pageBuilder: (_, __, ___) => page,
          transitionsBuilder: (_, animation, secondaryAnimation, child) {
            final slide = Tween<Offset>(begin: const Offset(0, 0.06), end: Offset.zero)
                .animate(CurvedAnimation(parent: animation, curve: Curves.easeOutCubic));
            return FadeTransition(
              opacity: CurvedAnimation(parent: animation, curve: Curves.easeOut),
              child: SlideTransition(position: slide, child: child),
            );
          },
        );
}

class ConfirmRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  ConfirmRoute({required this.page})
      : super(
          transitionDuration: const Duration(milliseconds: 500),
          reverseTransitionDuration: const Duration(milliseconds: 300),
          pageBuilder: (_, __, ___) => page,
          transitionsBuilder: (_, animation, __, child) {
            final scale = Tween<double>(begin: 0.92, end: 1.0)
                .animate(CurvedAnimation(parent: animation, curve: Curves.easeOutBack));
            return FadeTransition(
              opacity: CurvedAnimation(parent: animation, curve: Curves.easeIn),
              child: ScaleTransition(scale: scale, child: child),
            );
          },
        );
}

class FadeRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  FadeRoute({required this.page})
      : super(
          transitionDuration: const Duration(milliseconds: 400),
          pageBuilder: (_, __, ___) => page,
          transitionsBuilder: (_, animation, __, child) {
            return FadeTransition(
              opacity: Tween<double>(begin: 0.0, end: 1.0)
                  .animate(CurvedAnimation(parent: animation, curve: Curves.easeIn)),
              child: child,
            );
          },
        );
}

class SlideRightRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  SlideRightRoute({required this.page})
      : super(
          transitionDuration: const Duration(milliseconds: 400),
          pageBuilder: (_, __, ___) => page,
          transitionsBuilder: (_, animation, __, child) {
            final slide = Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero)
                .animate(CurvedAnimation(parent: animation, curve: Curves.easeOutCubic));
            return SlideTransition(position: slide, child: child);
          },
        );
}

class ScalePopRoute<T> extends PageRouteBuilder<T> {
  final Widget page;
  ScalePopRoute({required this.page})
      : super(
          transitionDuration: const Duration(milliseconds: 450),
          pageBuilder: (_, __, ___) => page,
          transitionsBuilder: (_, animation, secondaryAnimation, child) {
            final scale = Tween<double>(begin: 0.85, end: 1.0)
                .animate(CurvedAnimation(parent: animation, curve: Curves.easeOutBack));
            final fade = Tween<double>(begin: 0.0, end: 1.0)
                .animate(CurvedAnimation(parent: animation, curve: Curves.easeOut));
            return FadeTransition(
              opacity: fade,
              child: ScaleTransition(scale: scale, child: child),
            );
          },
        );
}
