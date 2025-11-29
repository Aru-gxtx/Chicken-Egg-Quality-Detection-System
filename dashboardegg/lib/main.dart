import 'package:flutter/material.dart';
import 'pages/dashboard_page.dart';
import 'pages/analytics_page.dart';

void main() {
  runApp(EggApp());
}

class EggApp extends StatefulWidget {
  @override
  _EggAppState createState() => _EggAppState();
}

class _EggAppState extends State<EggApp> {
  int _selectedIndex = 0;
  final List<Widget> _pages = [EggDashboard(), AnalyticsPage()];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Egg Quality System',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: Scaffold(
        body: _pages[_selectedIndex],
        bottomNavigationBar: NavigationBar(
          selectedIndex: _selectedIndex,
          onDestinationSelected: _onItemTapped,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
            NavigationDestination(icon: Icon(Icons.analytics), label: 'Analytics'),
          ],
        ),
      ),
    );
  }
}
