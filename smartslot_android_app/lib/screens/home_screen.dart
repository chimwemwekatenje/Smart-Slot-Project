import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'resources_screen.dart';
import 'my_bookings_screen.dart';
import 'org_panel_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    // External users: Resources + Profile only
    // Employees: Resources + My Bookings + Profile
    // OrgAdmin: Resources + My Bookings + Org Panel + Profile
    final List<Widget> tabs;
    final List<BottomNavigationBarItem> navItems;

    if (auth.isExternal) {
      tabs = [
        const ResourcesScreen(),
        const ProfileScreen(),
      ];
      navItems = const [
        BottomNavigationBarItem(
            icon: Icon(Icons.explore_outlined), label: 'Explore'),
        BottomNavigationBarItem(
            icon: Icon(Icons.person_outline), label: 'Profile'),
      ];
    } else if (auth.isOrgAdmin) {
      tabs = [
        const ResourcesScreen(),
        const MyBookingsScreen(),
        const OrgPanelScreen(),
        const ProfileScreen(),
      ];
      navItems = const [
        BottomNavigationBarItem(
            icon: Icon(Icons.grid_view_rounded), label: 'Resources'),
        BottomNavigationBarItem(
            icon: Icon(Icons.calendar_today_outlined), label: 'My Bookings'),
        BottomNavigationBarItem(
            icon: Icon(Icons.business_outlined), label: 'Org Panel'),
        BottomNavigationBarItem(
            icon: Icon(Icons.person_outline), label: 'Profile'),
      ];
    } else {
      // Employee
      tabs = [
        const ResourcesScreen(),
        const MyBookingsScreen(),
        const ProfileScreen(),
      ];
      navItems = const [
        BottomNavigationBarItem(
            icon: Icon(Icons.grid_view_rounded), label: 'Resources'),
        BottomNavigationBarItem(
            icon: Icon(Icons.calendar_today_outlined), label: 'My Bookings'),
        BottomNavigationBarItem(
            icon: Icon(Icons.person_outline), label: 'Profile'),
      ];
    }

    // Clamp index when tab count changes
    final safeIndex = _currentIndex.clamp(0, tabs.length - 1);

    return Scaffold(
      body: IndexedStack(
        index: safeIndex,
        children: tabs,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: safeIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: navItems,
      ),
    );
  }
}
