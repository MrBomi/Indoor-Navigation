import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:flutter_compass/flutter_compass.dart';

import '../../models/user_location.dart';

class PdrService extends ChangeNotifier {
  static final PdrService _instance = PdrService._internal();
  factory PdrService() => _instance;
  PdrService._internal();

  // PDR State
  bool _isPdrRunning = false;
  double _pdrNorthOffset = 0.0;
  double? _headingDeg;
  int _pdrSteps = 0;
  final double _stepLengthMeters = 0.70;
  final int _minStepIntervalMs = 250;
  int _lastStepMs = 0;

  // Sensor subscriptions
  StreamSubscription? _accSub;
  StreamSubscription? _compassSub;
  double _emaMag = 0.0;
  final double _smoothAlpha = 0.2;
  final double _stepThreshold = 1.2;
  double _prevEmaMag = 0.0;

  // Coordinate conversion
  double _metersToPixelScale = 8.5;
  double _svgWidth = 800;
  double _svgHeight = 800;

  UserLocation? _currentLocation;

  // Getters
  bool get isPdrRunning => _isPdrRunning;
  double get pdrNorthOffset => _pdrNorthOffset;
  double? get headingDeg => _headingDeg;
  int get pdrSteps => _pdrSteps;
  UserLocation? get currentLocation => _currentLocation;

  // Setters
  void setSvgDimensions(double width, double height) {
    _svgWidth = width;
    _svgHeight = height;
  }

  void setMetersToPixelScale(double scale) {
    _metersToPixelScale = scale;
  }

  void setNorthOffset(double offset) {
    _pdrNorthOffset = offset;
    notifyListeners();
  }

  void setInitialLocation(UserLocation location) {
    _currentLocation = location;
    notifyListeners();
  }

  void startPdr() {
    if (_isPdrRunning || _currentLocation == null) return;

    _isPdrRunning = true;
    _startSensors();
    notifyListeners();
  }

  void _startSensors() {
    // Start compass
    _compassSub = FlutterCompass.events?.listen((event) {
      _headingDeg = event.heading;
      notifyListeners();
    });

    // Start accelerometer
    _accSub = userAccelerometerEventStream().listen(_handleAccelerometerEvent);
  }

  void _handleAccelerometerEvent(UserAccelerometerEvent event) {
    final nowMs = DateTime.now().millisecondsSinceEpoch;
    final mag = sqrt(event.x * event.x + event.y * event.y + event.z * event.z);

    _emaMag = (1 - _smoothAlpha) * _emaMag + _smoothAlpha * mag;

    final bool rising = _prevEmaMag <= _stepThreshold && _emaMag > _stepThreshold;
    final bool spaced = (nowMs - _lastStepMs) > _minStepIntervalMs;

    if (rising && spaced && _currentLocation != null) {
      _lastStepMs = nowMs;
      _pdrSteps += 1;
      _updateLocationWithStep();
    }

    _prevEmaMag = _emaMag;
  }

  void _updateLocationWithStep() {
    if (_currentLocation == null) return;

    // Convert current SVG coordinates back to meters for calculation
    final currentMeterX = (_currentLocation!.x - _svgWidth / 2) / _metersToPixelScale;
    final currentMeterY = (_svgHeight / 2 - _currentLocation!.y) / _metersToPixelScale;

    // Calculate movement with north offset compensation
    final double adjustedHeading = ((_headingDeg ?? 0.0) + _pdrNorthOffset) * pi / 180.0;
    final newMeterX = currentMeterX + _stepLengthMeters * sin(adjustedHeading);
    final newMeterY = currentMeterY + _stepLengthMeters * cos(adjustedHeading);

    // Convert back to SVG coordinates
    final svgX = (_svgWidth / 2) + (newMeterX * _metersToPixelScale);
    final svgY = (_svgHeight / 2) - (newMeterY * _metersToPixelScale);

    _currentLocation = UserLocation(x: svgX, y: svgY);
    notifyListeners();
  }

  void stopPdr() {
    _isPdrRunning = false;
    _accSub?.cancel();
    _accSub = null;
    _compassSub?.cancel();
    _compassSub = null;
    notifyListeners();
  }

  void resetPdr() {
    _pdrSteps = 0;
    _lastStepMs = 0;
    _emaMag = 0;
    _prevEmaMag = 0;
    notifyListeners();
  }

  String getCurrentPositionInMeters() {
    if (_currentLocation == null) return "0.0m, 0.0m";

    final meterX = (_currentLocation!.x - _svgWidth / 2) / _metersToPixelScale;
    final meterY = (_svgHeight / 2 - _currentLocation!.y) / _metersToPixelScale;

    return "${meterX.toStringAsFixed(1)}m, ${meterY.toStringAsFixed(1)}m";
  }

  @override
  void dispose() {
    stopPdr();
    super.dispose();
  }
}