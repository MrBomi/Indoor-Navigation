import 'dart:async';
import 'dart:math';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:flutter_compass/flutter_compass.dart';
import '../../models/user_location.dart';

// Callback types
typedef LocationUpdateCallback = void Function(UserLocation? location);
typedef FeaturesUpdateCallback = void Function(Map<String, double>? features);
typedef CalibrationUpdateCallback = void Function(bool isCalibrating, bool isCalibrated, int samples, int target);

class MagneticPositioningService {
  // Streams and subscriptions
  StreamSubscription<MagnetometerEvent>? _magSubscription;
  StreamSubscription<CompassEvent>? _compassSubscription;

  // Real-time data
  double? _heading;
  Map<String, double>? _features;

  // Calibration state
  bool _isCalibrating = false;
  int _calibSamples = 0;
  static const int _calibTarget = 500;
  double _minX = double.infinity, _minY = double.infinity, _minZ = double.infinity;
  double _maxX = -double.infinity, _maxY = -double.infinity, _maxZ = -double.infinity;
  late double _biasX, _biasY, _biasZ;
  late double _scaleX, _scaleY, _scaleZ;
  bool _calibrated = false;

  // Callbacks
  FeaturesUpdateCallback? _onFeaturesUpdate;
  CalibrationUpdateCallback? _onCalibrationUpdate;

  // Collection of scanned points
  final Map<String, Map<String, double>> _collectedData = {};

  // Getters
  Map<String, double>? get currentFeatures => _features;
  bool get isCalibrated => _calibrated;
  bool get isCalibrating => _isCalibrating;
  int get calibrationSamples => _calibSamples;
  int get calibrationTarget => _calibTarget;
  Map<String, Map<String, double>> get collectedData => Map.from(_collectedData);

  // Initialize the service
  void initialize({
    FeaturesUpdateCallback? onFeaturesUpdate,
    CalibrationUpdateCallback? onCalibrationUpdate,
  }) {
    _onFeaturesUpdate = onFeaturesUpdate;
    _onCalibrationUpdate = onCalibrationUpdate;

    // Subscribe to heading
    final compassStream = FlutterCompass.events;
    if (compassStream != null) {
      _compassSubscription = compassStream.listen((event) {
        final hv = event.heading;
        if (hv != null) _heading = hv;
      });
    }

    // Subscribe to magnetometer
    _magSubscription = magnetometerEventStream().listen((event) {
      _processMag(event.x, event.y, event.z);
    });
  }

  // Process magnetometer data
  void _processMag(double mx, double my, double mz) {
    // Calibration tracking
    if (_isCalibrating) {
      _minX = min(_minX, mx); _minY = min(_minY, my); _minZ = min(_minZ, mz);
      _maxX = max(_maxX, mx); _maxY = max(_maxY, my); _maxZ = max(_maxZ, mz);
      _calibSamples++;

      if (_calibSamples >= _calibTarget) {
        _biasX = (_maxX + _minX) / 2;
        _biasY = (_maxY + _minY) / 2;
        _biasZ = (_maxZ + _minZ) / 2;
        _scaleX = (_maxX - _minX) / 2;
        _scaleY = (_maxY - _minY) / 2;
        _scaleZ = (_maxZ - _minZ) / 2;
        _isCalibrating = false;
        _calibrated = true;
      }

      _onCalibrationUpdate?.call(_isCalibrating, _calibrated, _calibSamples, _calibTarget);
    }

    // Normalize
    final nx = _calibrated ? (mx - _biasX) / _scaleX : mx;
    final ny = _calibrated ? (my - _biasY) / _scaleY : my;
    final nz = _calibrated ? (mz - _biasZ) / _scaleZ : mz;

    // Compute vector
    final magnitude = sqrt(nx * nx + ny * ny + nz * nz);
    final declination = _heading ?? (atan2(ny, nx) * 180 / pi);
    final inclination = atan2(nz, sqrt(nx * nx + ny * ny)) * 180 / pi;

    _features = {
      'nx': nx,
      'ny': ny,
      'nz': nz,
      'magnitude': magnitude,
      'declination': declination,
      'inclination': inclination,
    };

    _onFeaturesUpdate?.call(_features);
  }

  // Start calibration process
  void startCalibration() {
    _isCalibrating = true;
    _calibSamples = 0;
    _minX = _minY = _minZ = double.infinity;
    _maxX = _maxY = _maxZ = -double.infinity;
    _onCalibrationUpdate?.call(_isCalibrating, _calibrated, _calibSamples, _calibTarget);
  }

  // Scan and capture a point with averaging
  Future<bool> scanAndCapture(String pointName) async {
    if (pointName.isEmpty || _features == null) return false;

    // Collect ~30 samples over 1 second
    final List<Map<String, double>> buffer = [];
    for (int i = 0; i < 30; i++) {
      if (_features != null) buffer.add(Map.from(_features!));
      await Future.delayed(const Duration(milliseconds: 33));
    }

    if (buffer.isEmpty) return false;

    // Compute average
    final avg = <String, double>{};
    for (var key in buffer.first.keys) {
      avg[key] = buffer.map((e) => e[key]!).reduce((a, b) => a + b) / buffer.length;
    }

    _collectedData[pointName] = avg;
    return true;
  }

  // Remove a collected point
  void removeCollectedPoint(String pointName) {
    _collectedData.remove(pointName);
  }

  // Clear all collected data
  void clearCollectedData() {
    _collectedData.clear();
  }

  // Dispose resources
  void dispose() {
    _magSubscription?.cancel();
    _compassSubscription?.cancel();
    _magSubscription = null;
    _compassSubscription = null;
  }
}