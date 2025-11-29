import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:fl_chart/fl_chart.dart';

class AnalyticsPage extends StatefulWidget {
  @override
  _AnalyticsPageState createState() => _AnalyticsPageState();
}

class _AnalyticsPageState extends State<AnalyticsPage> {
  List<dynamic> eggs = [];
  Timer? refreshTimer;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchEggs();
    refreshTimer = Timer.periodic(Duration(seconds: 10), (timer) => fetchEggs());
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> fetchEggs() async {
    try {
      final response = await http.get(Uri.parse("http://10.210.3.169:8000/eggs")); //10.232.51.78
      if (response.statusCode == 200) {
        setState(() {
          eggs = json.decode(response.body)["eggs"];
          isLoading = false;
        });
      }
    } catch (e) {
      print("Error fetching analytics: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final gradeCounts = <String, int>{};
    final dailyCounts = <String, int>{};
    double avgConfidence = 0.0;

    for (var egg in eggs) {
      // Grade counts
      gradeCounts[egg["label"]] = (gradeCounts[egg["label"]] ?? 0) + 1;

      // Average confidence
      avgConfidence += (egg["confidence"] ?? 0);

      // Daily production
      final date = (egg["timestamp"] ?? "").split(" ")[0];
      if (date.isNotEmpty) {
        dailyCounts[date] = (dailyCounts[date] ?? 0) + 1;
      }
    }

    if (eggs.isNotEmpty) avgConfidence /= eggs.length;

    return Scaffold(
      appBar: AppBar(title: Text("Real-Time Analytics")),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildStatCard("Total Eggs", eggs.length.toString(), Icons.egg),
                  _buildStatCard("Avg. Confidence", "${(avgConfidence * 100).toStringAsFixed(1)}%", Icons.timeline),
                  SizedBox(height: 20),

                  Text("Production Over Time", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 10),
                  _buildLineChart(dailyCounts),

                  SizedBox(height: 30),
                  Text("Grade Distribution", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 10),
                  _buildPieChart(gradeCounts),
                ],
              ),
            ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Container(
      margin: EdgeInsets.symmetric(vertical: 8),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.teal.shade50,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 5)],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Icon(icon, color: Colors.teal, size: 32),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
              Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.teal)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPieChart(Map<String, int> gradeCounts) {
    final sections = gradeCounts.entries.map((e) {
      return PieChartSectionData(
        value: e.value.toDouble(),
        title: e.key,
        radius: 50,
      );
    }).toList();

    return Container(
      height: 220,
      child: PieChart(PieChartData(sections: sections)),
    );
  }

  Widget _buildLineChart(Map<String, int> dailyCounts) {
    final sortedKeys = dailyCounts.keys.toList()..sort();
    final spots = <FlSpot>[];
    for (int i = 0; i < sortedKeys.length; i++) {
      spots.add(FlSpot(i.toDouble(), dailyCounts[sortedKeys[i]]!.toDouble()));
    }

    return Container(
      height: 200,
      child: LineChart(
        LineChartData(
          titlesData: FlTitlesData(show: false),
          borderData: FlBorderData(show: true),
          lineBarsData: [
            LineChartBarData(
              isCurved: true,
              barWidth: 3,
              spots: spots,
              dotData: FlDotData(show: true),
            ),
          ],
        ),
      ),
    );
  }
}
