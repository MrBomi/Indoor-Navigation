import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:indigo_test/constants.dart';
import 'package:indigo_test/services/admin/positioning_service.dart';
import 'package:wifi_scan/wifi_scan.dart';
import 'package:path_provider/path_provider.dart';

import '../../models/Building.dart';
import '../../services/general.dart';
import '../../widgets/floor_picker.dart';
import '../../widgets/user_svg_view.dart';

class WifiCollectionFingerprint extends StatefulWidget {
  final Building building;

  const WifiCollectionFingerprint({
    super.key,
    required this.building,
  });

  @override
  _WifiCollectionFingerprintState createState() =>
      _WifiCollectionFingerprintState();
}

class _WifiCollectionFingerprintState extends State<WifiCollectionFingerprint> {
  int selectedFloor = 1;
  String? gridSvgData;
  List<int> floorsList = [];
  final GeneralService generalService = GeneralService();
  final PositioningService positioningService = PositioningService();

  // WiFi scanning state
  Timer? _scanTimer;
  List<WiFiAccessPoint> _currentAccessPoints = [];
  Map<String, double>? _currentFeatures;
  bool _isScanning = false;
  bool _canScan = false;

  // UI state
  final TextEditingController _pointController = TextEditingController();
  Map<String, Map<String, double>> _collectedData = {};
  bool _isCapturing = false;

  @override
  void initState() {
    super.initState();
    loadFloorsList();
    _initializeWiFi();
  }

  @override
  void dispose() {
    _scanTimer?.cancel();
    _pointController.dispose();
    super.dispose();
  }

  Future<void> _initializeWiFi() async {
    // Check if WiFi scan is supported
    final can = await WiFiScan.instance.canGetScannedResults();
    setState(() {
      _canScan = can == CanGetScannedResults.yes;
    });

    if (_canScan) {
      // Start periodic WiFi scanning
      _startPeriodicScanning();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('WiFi scanning is not available on this device'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _startPeriodicScanning() {
    _scanTimer?.cancel();
    _scanTimer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      if (!mounted) return;
      await _scanWiFi();
    });
  }

  Future<void> _scanWiFi() async {
    if (!_canScan) return;

    setState(() {
      _isScanning = true;
    });

    try {
      // Start scan
      await WiFiScan.instance.startScan();

      // Wait a bit for scan to complete
      await Future.delayed(const Duration(milliseconds: 1500));

      // Get results
      final results = await WiFiScan.instance.getScannedResults();

      if (mounted) {
        setState(() {
          _currentAccessPoints = results;
          _currentFeatures = _extractWiFiFeatures(results);
          _isScanning = false;
        });

        print('WiFi scan found ${results.length} access points');
        print('Features: $_currentFeatures');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isScanning = false;
        });
      }
      print('WiFi scan error: $e');
    }
  }

  Map<String, double> _extractWiFiFeatures(List<WiFiAccessPoint> accessPoints) {
    final features = <String, double>{};

    if (accessPoints.isEmpty) {
      return {'no_wifi_detected': -100.0};
    }

    // Extract RSSI for each BSSID (just like Android code)
    for (final ap in accessPoints) {
      features[ap.bssid] = ap.level.toDouble();
    }

    return features;
  }

  Future<void> _saveToCSV(String pointName, Map<String, double> wifiData) async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = File('${directory.path}/${widget.building.name}_floor${selectedFloor}.csv');

      // Read existing data
      final existingRows = <Map<String, String>>[];
      final allBssids = <String>{};
      List<String> header = ['Vertex'];

      if (await file.exists()) {
        final contents = await file.readAsString();
        final lines = contents.split('\n').where((line) => line.trim().isNotEmpty).toList();

        if (lines.isNotEmpty) {
          header = lines.first.split(',');
          allBssids.addAll(header.skip(1)); // skip 'Vertex'

          // Read existing rows
          for (int i = 1; i < lines.length; i++) {
            final parts = lines[i].split(',');
            if (parts.length == header.length) {
              final rowMap = <String, String>{};
              for (int j = 0; j < header.length; j++) {
                rowMap[header[j]] = parts[j];
              }
              existingRows.add(rowMap);
            }
          }
        }
      }

      // Add current scan BSSIDs
      allBssids.addAll(wifiData.keys);
      final sortedBssids = allBssids.toList()..sort();
      final newHeader = ['Vertex'] + sortedBssids;

      // Create new row
      final newRow = <String, String>{};
      newRow['Vertex'] = pointName;
      for (final bssid in sortedBssids) {
        newRow[bssid] = wifiData[bssid]?.toString() ?? '-100';
      }

      // Prepare CSV content
      final csvLines = <String>[];
      csvLines.add(newHeader.join(','));

      // Add existing rows with updated structure
      for (final row in existingRows) {
        final fullRow = newHeader.map((col) => row[col] ?? '-100').toList();
        csvLines.add(fullRow.join(','));
      }

      // Add new row
      final newLine = newHeader.map((col) => newRow[col] ?? '-100').toList();
      csvLines.add(newLine.join(','));

      // Write to file
      await file.writeAsString(csvLines.join('\n'));

       print('CSV saved to: ${file.path}');

    } catch (e) {
      print('Error saving CSV: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error saving CSV file')),
      );
    }
  }

  Future<void> _scanAndCapture() async {
    final name = _pointController.text.trim();
    if (name.isEmpty || _currentFeatures == null || _currentFeatures!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a point name and ensure WiFi data is available')),
      );
      return;
    }

    // Show loading state
    setState(() {
      _isCapturing = true;
    });

    try {
      // Collect 10 separate samples
      final List<Map<String, double>> samples = [];

      for (int i = 0; i < 10; i++) {
        await _scanWiFi();
        if (_currentFeatures != null && _currentFeatures!.isNotEmpty) {
          samples.add(Map.from(_currentFeatures!));
        }
        await Future.delayed(const Duration(milliseconds: 300));
      }

      if (samples.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to collect WiFi data samples')),
        );
        return;
      }

      // Save each sample as a separate line in CSV
      for (int i = 0; i < samples.length; i++) {
        await _saveToCSV(name, samples[i]);
      }

      // For server sending, use the first sample (or you could average if needed for server)
      final firstSample = samples.first;
      setState(() {
        _collectedData[name] = firstSample;
        _pointController.clear();
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Point "$name" captured with ${samples.length} separate samples!')),
      );
    } finally {
      // Hide loading state
      setState(() {
        _isCapturing = false;
      });
    }
  }

  Future<void> _sendAllData() async {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/${widget.building.name}_floor${selectedFloor}.csv');

    final success = await positioningService.sendFingerprintCsvFile(
        Constants.sendFingerprint,
        file,
        widget.building.buildingId,
        selectedFloor,
    );

    if (success == true) {
      try {
        if (await file.exists()) {
          await file.delete();
        }
      } catch (e) {
        debugPrint('Error deleting file: $e');
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('WiFi training data sent successfully!')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to send WiFi training data.')),
      );
    }
  }

  Future<void> loadFloorsList() async {
    try {
      final list = await generalService.getFloors(
        buildingId: widget.building.buildingId,
      );

      if (!mounted) return;
      setState(() {
        floorsList = list;
        if (list.isNotEmpty) {
          selectedFloor = list.first;
        }
      });

      if (floorsList.isNotEmpty) {
        await loadSvg();
      }
    } catch (e) {
      debugPrint('Error loading floor list: $e');
    }
  }

  Future<void> loadSvg() async {
    final url = Uri.parse(Constants.getGridSvg);
    gridSvgData = await generalService.sendSvgRequest(
        url: url,
        method: "GET",
        queryParams: {
          'buildingId': widget.building.buildingId.toString(),
          'floorId': selectedFloor.toString(),
        }
    );
    setState(() {});
  }

  Widget _buildControlsBottomSheet() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Point name input
            TextField(
              controller: _pointController,
              decoration: const InputDecoration(
                labelText: 'Point Name',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.location_on),
              ),
            ),
            const SizedBox(height: 12),

            // Button row
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: (_currentFeatures != null &&
                        _currentFeatures!.isNotEmpty &&
                        _pointController.text.trim().isNotEmpty &&
                        !_isCapturing)
                        ? _scanAndCapture
                        : null,
                    icon: _isCapturing
                        ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                        : const Icon(Icons.wifi),
                    label: Text(_isCapturing ? 'Capturing...' : 'Scan & Capture'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _collectedData.isEmpty ? null : _sendAllData,
                    icon: const Icon(Icons.send),
                    label: const Text('Send All'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),

            // Collected points count and WiFi info
            if (_collectedData.isNotEmpty || _currentAccessPoints.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Column(
                  children: [
                    if (_collectedData.isNotEmpty)
                      Text(
                        'Collected points: ${_collectedData.length}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    if (_currentAccessPoints.isNotEmpty)
                      Text(
                        'WiFi APs detected: ${_currentAccessPoints.length}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.blue,
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  double _getBottomSheetHeight() {
    double baseHeight = 140;
    if (_collectedData.isNotEmpty || _currentAccessPoints.isNotEmpty) {
      baseHeight += 50; // Extra space for WiFi info
    }
    return baseHeight + MediaQuery.of(context).padding.bottom;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.building.name} - WiFi Positioning'),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    FloorPickerButton(
                      floorsList: floorsList,
                      selectedFloor: selectedFloor,
                      onFloorSelected: (value) {
                        setState(() => selectedFloor = value);
                        loadSvg();
                      },
                    ),
                    const Spacer(),
                    // WiFi status indicator
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: _canScan
                            ? (_currentAccessPoints.isNotEmpty ? Colors.green : Colors.orange)
                            : Colors.red,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _isScanning
                                ? Icons.wifi_find
                                : (_canScan
                                ? (_currentAccessPoints.isNotEmpty ? Icons.wifi : Icons.wifi_off)
                                : Icons.error),
                            size: 16,
                            color: Colors.white,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _isScanning
                                ? 'Scanning...'
                                : (_canScan
                                ? '${_currentAccessPoints.length} APs'
                                : 'WiFi Unavailable'),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Container(
                  margin: EdgeInsets.only(bottom: _getBottomSheetHeight()),
                  child: gridSvgData == null
                      ? const Center(child: CircularProgressIndicator())
                      : ZoomableSvgView(rawSvg: gridSvgData!),
                ),
              ),
            ],
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: _buildControlsBottomSheet(),
          ),
        ],
      ),
    );
  }
}