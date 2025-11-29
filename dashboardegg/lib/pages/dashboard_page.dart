import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:fl_chart/fl_chart.dart';

class EggDashboardApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Egg Quality Dashboard',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: EggDashboard(),
    );
  }
}

class EggDashboard extends StatefulWidget {
  @override
  _EggDashboardState createState() => _EggDashboardState();
}

class _EggDashboardState extends State<EggDashboard> {
  List<dynamic> eggs = [];
  bool isLoading = true;
  Timer? refreshTimer;
  String sortOption = "Date (Most Recent)";

  @override
  void initState() {
    super.initState();
    fetchEggs();

    // 🔁 Auto-refresh every 5 seconds
    refreshTimer = Timer.periodic(Duration(seconds: 5), (timer) {
      fetchEggs();
    });
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    refreshTimer = null;
    super.dispose();
  }

  Future<void> fetchEggs() async {
    try {
      final response = await http.get(
        Uri.parse("http://10.210.3.169:8000/eggs"),
        //10.232.51.78
      );
      if (response.statusCode == 200) {
        if (!mounted) return; // ✅ avoid calling setState after dispose
        setState(() {
          eggs = json.decode(response.body)["eggs"];
          applySorting();
          isLoading = false;
        });
      } else {
        throw Exception("Failed to load eggs");
      }
    } catch (e) {
      print("Error: $e");
      if (!mounted) return;
      setState(() => isLoading = false);
    }
  }

  // 🕒 Format timestamp
  String formatTimestamp(String raw) {
    try {
      if (raw.contains("_")) {
        final datePart = raw.split("_")[0];
        final timePart = raw.split("_")[1];
        final year = datePart.substring(0, 4);
        final month = datePart.substring(4, 6);
        final day = datePart.substring(6, 8);
        final hour = timePart.substring(0, 2);
        final minute = timePart.substring(2, 4);
        final second = timePart.substring(4, 6);
        return "$month-$day-$year $hour:$minute:$second";
      }

      if (raw.contains("-") && raw.contains(":")) {
        final parts = raw.split(" ");
        final date = parts[0].split("-");
        final time = parts[1];
        return "${date[1]}-${date[2]}-${date[0]} $time";
      }

      return raw;
    } catch (e) {
      return raw;
    }
  }

  // 🧮 Sorting logic
  void applySorting() {
    if (!mounted) return;
    setState(() {
      if (sortOption == "Date (Most Recent)") {
        eggs.sort((a, b) => b["timestamp"].compareTo(a["timestamp"]));
      } else if (sortOption == "Grade") {
        eggs.sort((a, b) => a["label"].toString().compareTo(b["label"].toString()));
      } else if (sortOption == "Size") {
        eggs.sort((a, b) => a["size"].toString().compareTo(b["size"].toString()));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final totalEggs = eggs.length;
    final labelCounts = <String, int>{};
    for (var egg in eggs) {
      labelCounts[egg["label"]] = (labelCounts[egg["label"]] ?? 0) + 1;
    }

    // 🎨 Predefined colors for chart
    final List<Color> pieColors = [
      Colors.teal,
      Colors.orange,
      Colors.blue,
      Colors.pink,
      Colors.purple,
      Colors.green,
      Colors.amber,
      Colors.redAccent,
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text("Egg Quality Dashboard"),
        actions: [IconButton(icon: Icon(Icons.refresh), onPressed: fetchEggs)],
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : eggs.isEmpty
              ? Center(child: Text("No eggs found"))
              : SingleChildScrollView(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    children: [
                      // Summary cards
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildSummaryCard(Icons.egg, "Total Eggs", "$totalEggs"),
                          _buildSummaryCard(
                            Icons.star,
                            "Labels",
                            "${labelCounts.keys.length} types",
                          ),
                        ],
                      ),
                      SizedBox(height: 20),

                      // Label distribution chart
                      if (labelCounts.isNotEmpty)
                        Container(
                          height: 220,
                          padding: EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(color: Colors.black12, blurRadius: 6),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Label Distribution",
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 10),
                              Expanded(
                                child: PieChart(
                                  PieChartData(
                                    sections: labelCounts.entries
                                        .toList()
                                        .asMap()
                                        .entries
                                        .map((entry) {
                                      int index = entry.key;
                                      var data = entry.value;
                                      return PieChartSectionData(
                                        value: data.value.toDouble(),
                                        title: data.key,
                                        color: pieColors[index % pieColors.length], // 🆕 color per slice
                                        radius: 55,
                                        titleStyle: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.white,
                                        ),
                                      );
                                    }).toList(),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      SizedBox(height: 20),

                      // 🆕 Sorting dropdown
                      Align(
                        alignment: Alignment.centerRight,
                        child: DropdownButton<String>(
                          value: sortOption,
                          items: [
                            "Date (Most Recent)",
                            "Grade",
                            "Size",
                          ].map((e) {
                            return DropdownMenuItem(
                              value: e,
                              child: Text(e),
                            );
                          }).toList(),
                          onChanged: (value) {
                            setState(() {
                              sortOption = value!;
                              applySorting();
                            });
                          },
                        ),
                      ),

                      // Egg list
                      ListView.builder(
                        shrinkWrap: true,
                        physics: NeverScrollableScrollPhysics(),
                        itemCount: eggs.length,
                        itemBuilder: (context, index) {
                          final egg = eggs[index];
                          final rawTimestamp = egg["timestamp"] ?? "Unknown";
                          final formattedTime = formatTimestamp(rawTimestamp);
                          final confidence =
                              (egg["confidence"] * 100).toStringAsFixed(1);

                          return Card(
                            elevation: 3,
                            margin: EdgeInsets.only(bottom: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: ListTile(
                              contentPadding: EdgeInsets.all(12),
                              leading: ClipRRect(
                                borderRadius: BorderRadius.circular(8),
                                child: Image.network(
                                  "http://10.210.3.169:8000/images/${Uri.encodeComponent(egg["image_path"].split('/').last)}",
                                  //10.232.51.78
                                  width: 70,
                                  height: 70,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) =>
                                      Icon(Icons.broken_image, size: 60),
                                ),
                              ),
                              title: Text(
                                egg["label"],
                                style: TextStyle(fontWeight: FontWeight.bold),
                              ),
                              subtitle: Text(
                                "Size: ${egg["size"]}\n"
                                "Confidence: $confidence%\n"
                                "Captured: $formattedTime",
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
    );
  }

  Widget _buildSummaryCard(IconData icon, String label, String value) {
    return Container(
      width: 160,
      height: 100,
      decoration: BoxDecoration(
        color: Colors.teal.shade50,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4)],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: Colors.teal, size: 30),
          SizedBox(height: 8),
          Text(
            label,
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.teal,
            ),
          ),
        ],
      ),
    );
  }
}
