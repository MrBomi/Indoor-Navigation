// import 'dart:async';
// import 'dart:convert';
// import 'dart:math';
// import 'package:flutter/material.dart';
// import 'package:indigo_test/constants.dart';
// import 'package:sensors_plus/sensors_plus.dart';
// import 'package:flutter_compass/flutter_compass.dart';
// import 'package:http/http.dart' as http;
//
// import '../../models/Building.dart';
// import '../../services/admin/positioning_service.dart';
// import '../../services/general.dart';
// import '../../widgets/floor_picker.dart';
// import '../../widgets/user_svg_view.dart';
//
// class MagneticPositioningWithCompass extends StatefulWidget {
//   final Building building;
//
//   const MagneticPositioningWithCompass({
//     super.key,
//     required this.building,
//   });
//
//   @override
//   _MagneticPositioningWithCompassState createState() =>
//       _MagneticPositioningWithCompassState();
// }
//
// class _MagneticPositioningWithCompassState extends State<MagneticPositioningWithCompass> {
//   StreamSubscription<MagnetometerEvent>? _magSubscription;
//   StreamSubscription<CompassEvent>? _compassSubscription;
//   int selectedFloor = 1;
//   String? gridSvgData;
//   List<int> floorsList = [];
//   final GeneralService generalService = GeneralService();
//   final PositioningService positioningService = PositioningService();
//
//   // Real-time heading and features
//   double? _heading;
//   Map<String, double>? _features;
//
//   // Calibration state
//   bool _isCalibrating = false;
//   int _calibSamples = 0;
//   static const int _calibTarget = 500;
//   double _minX = double.infinity, _minY = double.infinity, _minZ = double.infinity;
//   double _maxX = -double.infinity, _maxY = -double.infinity, _maxZ = -double.infinity;
//   late double _biasX, _biasY, _biasZ;
//   late double _scaleX, _scaleY, _scaleZ;
//   bool _calibrated = false;
//
//   // Collection of scanned points
//   final TextEditingController _pointController = TextEditingController();
//   final Map<String, Map<String, double>> _collectedData = {};
//
//   @override
//   void initState() {
//     super.initState();
//     loadFloorsList();
//
//     // Subscribe to heading
//     final compassStream = FlutterCompass.events;
//     if (compassStream != null) {
//       _compassSubscription = compassStream.listen((event) {
//         final hv = event.heading;
//         if (hv != null) setState(() => _heading = hv);
//       });
//     }
//
//     // Subscribe to magnetometer
//     _magSubscription = magnetometerEventStream().listen((event) {
//       _processMag(event.x, event.y, event.z);
//     });
//   }
//
//   void _processMag(double mx, double my, double mz) {
//     // Calibration tracking
//     if (_isCalibrating) {
//       _minX = min(_minX, mx); _minY = min(_minY, my); _minZ = min(_minZ, mz);
//       _maxX = max(_maxX, mx); _maxY = max(_maxY, my); _maxZ = max(_maxZ, mz);
//       _calibSamples++;
//       if (_calibSamples >= _calibTarget) {
//         _biasX = (_maxX + _minX) / 2;
//         _biasY = (_maxY + _minY) / 2;
//         _biasZ = (_maxZ + _minZ) / 2;
//         _scaleX = (_maxX - _minX) / 2;
//         _scaleY = (_maxY - _minY) / 2;
//         _scaleZ = (_maxZ - _minZ) / 2;
//         setState(() { _isCalibrating = false; _calibrated = true; });
//       }
//     }
//
//     // Normalize
//     final nx = _calibrated ? (mx - _biasX) / _scaleX : mx;
//     final ny = _calibrated ? (my - _biasY) / _scaleY : my;
//     final nz = _calibrated ? (mz - _biasZ) / _scaleZ : mz;
//
//     // Compute vector
//     final magnitude = sqrt(nx * nx + ny * ny + nz * nz);
//     final declination = _heading ?? (atan2(ny, nx) * 180 / pi);
//     final inclination = atan2(nz, sqrt(nx * nx + ny * ny)) * 180 / pi;
//
//     setState(() {
//       _features = {
//         'nx': nx,
//         'ny': ny,
//         'nz': nz,
//         'magnitude': magnitude,
//         'declination': declination,
//         'inclination': inclination,
//       };
//     });
//     print('Feature Vector: $_features');
//   }
//
//   @override
//   void dispose() {
//     _magSubscription?.cancel();
//     _compassSubscription?.cancel();
//     _pointController.dispose();
//     super.dispose();
//   }
//
//   void _startCalibration() {
//     setState(() {
//       _isCalibrating = true;
//       _calibSamples = 0;
//       _minX = _minY = _minZ = double.infinity;
//       _maxX = _maxY = _maxZ = -double.infinity;
//     });
//   }
//
//   Future<void> _scanAndCapture() async {
//     final name = _pointController.text.trim();
//     if (name.isEmpty || _features == null) return;
//
//     // Collect ~30 samples over 1 second
//     final List<Map<String, double>> buffer = [];
//     for (int i = 0; i < 30; i++) {
//       if (_features != null) buffer.add(Map.from(_features!));
//       await Future.delayed(const Duration(milliseconds: 33));
//     }
//
//     // Compute average
//     final avg = <String, double>{};
//     for (var key in buffer.first.keys) {
//       avg[key] = buffer.map((e) => e[key]!).reduce((a, b) => a + b) / buffer.length;
//     }
//
//     setState(() {
//       _collectedData[name] = avg;
//       _pointController.clear(); // Clear the text field after capturing
//     });
//
//     // Show confirmation
//     ScaffoldMessenger.of(context).showSnackBar(
//       SnackBar(content: Text('Point "$name" captured successfully!')),
//     );
//   }
//
//   Future<void> loadFloorsList() async {
//     try {
//       final list = await generalService.getFloors(
//         buildingId: widget.building.buildingId,
//       );
//
//       if (!mounted) return;
//       setState(() {
//         floorsList = list;
//         // pick first floor as default, if there is one
//         if (list.isNotEmpty) {
//           selectedFloor = list.first;
//         }
//       });
//
//       // now that we have a floor, load its SVG
//       if (floorsList.isNotEmpty) {
//         await loadSvg();
//       }
//     } catch (e) {
//       debugPrint('Error loading floor list: $e');
//     }
//   }
//
//   Future<void> loadSvg() async {
//     final url = Uri.parse(Constants.getGridSvg);
//     gridSvgData = await generalService.sendSvgRequest(
//         url: url,
//         method: "GET",
//         queryParams: {
//           'buildingId': widget.building.buildingId.toString(),
//           'floorId': selectedFloor.toString(),
//         }
//     );
//     setState(() {});
//   }
//
//   Widget _buildControlsBottomSheet() {
//     return Container(
//       padding: const EdgeInsets.all(16.0),
//       decoration: const BoxDecoration(
//         color: Colors.white,
//         borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
//         boxShadow: [
//           BoxShadow(
//             color: Colors.black26,
//             blurRadius: 10,
//             offset: Offset(0, -2),
//           ),
//         ],
//       ),
//       child: SafeArea(
//         child: Column(
//           mainAxisSize: MainAxisSize.min,
//           children: [
//             // Point name input
//             TextField(
//               controller: _pointController,
//               decoration: const InputDecoration(
//                 labelText: 'Point Name',
//                 border: OutlineInputBorder(),
//                 prefixIcon: Icon(Icons.location_on),
//               ),
//             ),
//             const SizedBox(height: 12),
//
//             // Button row
//             Row(
//               children: [
//                 Expanded(
//                   child: ElevatedButton.icon(
//                     onPressed: (_features != null && _pointController.text.trim().isNotEmpty)
//                         ? _scanAndCapture
//                         : null,
//                     icon: const Icon(Icons.scanner),
//                     label: const Text('Scan & Capture'),
//                     style: ElevatedButton.styleFrom(
//                       padding: const EdgeInsets.symmetric(vertical: 12),
//                     ),
//                   ),
//                 ),
//                 const SizedBox(width: 12),
//                 Expanded(
//                   child: ElevatedButton.icon(
//                     onPressed: _collectedData.isEmpty
//                         ? null
//                         // : () => positioningService.sendAll
//                         : () => positioningService.sendData(
//                         Constants.train,
//                         widget.building.buildingId,
//                         selectedFloor,
//                         _collectedData
//                     ),
//                     icon: const Icon(Icons.send),
//                     label: const Text('Send All'),
//                     style: ElevatedButton.styleFrom(
//                       padding: const EdgeInsets.symmetric(vertical: 12),
//                     ),
//                   ),
//                 ),
//               ],
//             ),
//
//             // Collected points count
//             if (_collectedData.isNotEmpty)
//               Padding(
//                 padding: const EdgeInsets.only(top: 8),
//                 child: Text(
//                   'Collected points: ${_collectedData.length}',
//                   style: Theme.of(context).textTheme.bodySmall,
//                 ),
//               ),
//           ],
//         ),
//       ),
//     );
//   }
//
//   double _getBottomSheetHeight() {
//     // Calculate approximate height of bottom sheet
//     double baseHeight = 140; // Base height for text field and buttons
//     if (_collectedData.isNotEmpty) {
//       baseHeight += 30; // Add height for collected points text
//     }
//     return baseHeight + MediaQuery.of(context).padding.bottom;
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: Text('${widget.building.name} - Magnetic Positioning'),
//         centerTitle: true,
//       ),
//       body: Stack(
//         children: [
//           Column(
//             children: [
//               Padding(
//                 padding: const EdgeInsets.all(16.0),
//                 child: Row(
//                   children: [
//                     FloorPickerButton(
//                       floorsList: floorsList,
//                       selectedFloor: selectedFloor,
//                       onFloorSelected: (value) {
//                         setState(() => selectedFloor = value);
//                         loadSvg();
//                       },
//                     ),
//                     const Spacer(),
//                     // Calibration status indicator
//                     Container(
//                       padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
//                       decoration: BoxDecoration(
//                         color: _calibrated ? Colors.green : Colors.orange,
//                         borderRadius: BorderRadius.circular(20),
//                       ),
//                       child: Row(
//                         mainAxisSize: MainAxisSize.min,
//                         children: [
//                           Icon(
//                             _calibrated ? Icons.check_circle : Icons.warning,
//                             size: 16,
//                             color: Colors.white,
//                           ),
//                           const SizedBox(width: 4),
//                           Text(
//                             _calibrated ? 'Calibrated' : 'Not Calibrated',
//                             style: const TextStyle(
//                               color: Colors.white,
//                               fontSize: 12,
//                             ),
//                           ),
//                         ],
//                       ),
//                     ),
//                   ],
//                 ),
//               ),
//               Expanded(
//                 child: Container(
//                   margin: EdgeInsets.only(bottom: _getBottomSheetHeight()),
//                   child: gridSvgData == null
//                       ? const Center(child: CircularProgressIndicator())
//                       : ZoomableSvgView(rawSvg: gridSvgData!),
//                 ),
//               ),
//             ],
//           ),
//           Align(
//             alignment: Alignment.bottomCenter,
//             child: _buildControlsBottomSheet(),
//           ),
//         ],
//       ),
//       floatingActionButton: !_calibrated
//           ? FloatingActionButton(
//         onPressed: _startCalibration,
//         tooltip: 'Start Calibration',
//         child: const Icon(Icons.tune),
//       )
//           : null,
//     );
//   }
// }

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:indigo_test/constants.dart';
import 'package:indigo_test/services/admin/positioning_service.dart';

import '../../models/Building.dart';
import '../../services/general.dart';
import '../../services/dataCollection/data_collection.dart';
import '../../widgets/floor_picker.dart';
import '../../widgets/user_svg_view.dart';

class MagneticPositioningWithCompass extends StatefulWidget {
  final Building building;

  const MagneticPositioningWithCompass({
    super.key,
    required this.building,
  });

  @override
  _MagneticPositioningWithCompassState createState() =>
      _MagneticPositioningWithCompassState();
}

class _MagneticPositioningWithCompassState extends State<MagneticPositioningWithCompass> {
  int selectedFloor = 1;
  String? gridSvgData;
  List<int> floorsList = [];
  final GeneralService generalService = GeneralService();
  final MagneticPositioningService magneticService = MagneticPositioningService();
  final PositioningService positioningService = PositioningService();

  // UI state
  final TextEditingController _pointController = TextEditingController();
  Map<String, double>? _currentFeatures;
  bool _isCalibrated = false;
  bool _isCalibrating = false;
  int _calibSamples = 0;
  int _calibTarget = 500;
  Map<String, Map<String, double>> _collectedData = {};

  @override
  void initState() {
    super.initState();
    loadFloorsList();

    // Initialize magnetic positioning service
    magneticService.initialize(
      onFeaturesUpdate: (features) {
        if (mounted) {
          setState(() {
            _currentFeatures = features;
          });
        }
      },
      onCalibrationUpdate: (isCalibrating, isCalibrated, samples, target) {
        if (mounted) {
          setState(() {
            _isCalibrating = isCalibrating;
            _isCalibrated = isCalibrated;
            _calibSamples = samples;
            _calibTarget = target;
          });
        }
      },
    );
  }

  @override
  void dispose() {
    magneticService.dispose();
    _pointController.dispose();
    super.dispose();
  }

  void _startCalibration() {
    magneticService.startCalibration();
  }

  Future<void> _scanAndCapture() async {
    final name = _pointController.text.trim();
    if (name.isEmpty) return;

    final success = await magneticService.scanAndCapture(name);

    if (success) {
      setState(() {
        _collectedData = magneticService.collectedData;
        _pointController.clear();
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Point "$name" captured successfully!')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to capture point. Please try again.')),
      );
    }
  }

  Future<void> _sendAllData() async {
    final success = await positioningService.sendElectromagnetData(
       Constants.train,
        widget.building.buildingId,
        selectedFloor,
        _collectedData
    );
    print(success);
    if (success != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Training data sent successfully!')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to send training data.')),
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
                    onPressed: (_currentFeatures != null && _pointController.text.trim().isNotEmpty)
                        ? _scanAndCapture
                        : null,
                    icon: const Icon(Icons.scanner),
                    label: const Text('Scan & Capture'),
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

            // Collected points count
            if (_collectedData.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  'Collected points: ${_collectedData.length}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
          ],
        ),
      ),
    );
  }

  double _getBottomSheetHeight() {
    double baseHeight = 140;
    if (_collectedData.isNotEmpty) {
      baseHeight += 30;
    }
    return baseHeight + MediaQuery.of(context).padding.bottom;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.building.name} - Magnetic Positioning'),
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
                    // Calibration status indicator
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: _isCalibrated ? Colors.green : Colors.orange,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _isCalibrated ? Icons.check_circle : Icons.warning,
                            size: 16,
                            color: Colors.white,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _isCalibrated ? 'Calibrated' : 'Not Calibrated',
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
      floatingActionButton: !_isCalibrated
          ? FloatingActionButton(
        onPressed: _startCalibration,
        tooltip: 'Start Calibration',
        child: const Icon(Icons.tune),
      )
          : null,
    );
  }
}