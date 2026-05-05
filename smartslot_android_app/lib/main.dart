import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'providers/auth_provider.dart';
import 'providers/theme_provider.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
      ],
      child: const SmartSlotApp(),
    ),
  );
}

class SmartSlotApp extends StatelessWidget {
  const SmartSlotApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = context.watch<ThemeProvider>();
    return MaterialApp(
      title: 'SmartSlot',
      debugShowCheckedModeBanner: false,
      theme: lightTheme.copyWith(
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: _AppTransitionBuilder(),
            TargetPlatform.iOS: _AppTransitionBuilder(),
            TargetPlatform.windows: _AppTransitionBuilder(),
            TargetPlatform.linux: _AppTransitionBuilder(),
            TargetPlatform.macOS: _AppTransitionBuilder(),
          },
        ),
      ),
      darkTheme: darkTheme.copyWith(
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            TargetPlatform.android: _AppTransitionBuilder(),
            TargetPlatform.iOS: _AppTransitionBuilder(),
            TargetPlatform.windows: _AppTransitionBuilder(),
            TargetPlatform.linux: _AppTransitionBuilder(),
            TargetPlatform.macOS: _AppTransitionBuilder(),
          },
        ),
      ),
      themeMode: themeProvider.themeMode,
      initialRoute: '/',
      routes: {
        '/': (_) => const SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/register': (_) => const RegisterScreen(),
        '/home': (_) => const HomeScreen(),
      },
    );
  }
}

class _AppTransitionBuilder extends PageTransitionsBuilder {
  const _AppTransitionBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    final slide = Tween<Offset>(
      begin: const Offset(0, 0.05),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOutCubic));
    return FadeTransition(
      opacity: CurvedAnimation(parent: animation, curve: Curves.easeOut),
      child: SlideTransition(position: slide, child: child),
    );
  }
}
