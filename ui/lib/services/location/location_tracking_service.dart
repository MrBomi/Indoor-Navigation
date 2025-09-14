// services/location/location_tracking_service.dart
import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/user_location.dart';
import '../dataCollection/wifi_positioning_service.dart';
import '../admin/positioning_service.dart';
import '../../constants.dart';

class LocationTrackingService extends ChangeNotifier {
  static final LocationTrackingService _instance = LocationTrackingService._internal();
  factory LocationTrackingService() => _instance;
  LocationTrackingService._internal();

  final WifiPositioningService _wifiService = WifiPositioningService.instance;
  final PositioningService _positioningService = PositioningService();

  UserLocation? _userLocation;
  Timer? _locationTimer;
  bool _isLocationLoading = false;
  bool _isTrackingEnabled = false;

  // Store current context for fetching location
  int? _currentBuildingId;
  int? _currentFloor;

  // Getters
  UserLocation? get userLocation => _userLocation;
  bool get isLocationLoading => _isLocationLoading;
  bool get isTrackingEnabled => _isTrackingEnabled;

  Future<void> initialize() async {
    try {
      await _wifiService.init();
    } catch (e) {
      debugPrint('LocationTrackingService init error: $e');
      rethrow;
    }
  }

  void setContext({required int buildingId, required int floor}) {
    _currentBuildingId = buildingId;
    _currentFloor = floor;
  }

  void startTracking({int? buildingId, int? floor}) {
    if (_isTrackingEnabled) return;

    // Update context if provided
    if (buildingId != null) _currentBuildingId = buildingId;
    if (floor != null) _currentFloor = floor;

    if (_currentBuildingId == null || _currentFloor == null) {
      debugPrint('Cannot start tracking: buildingId or floor not set');
      return;
    }

    _isTrackingEnabled = true;
    _fetchUserLocation();
    _locationTimer = Timer.periodic(
      const Duration(seconds: 3),
          (_) => _fetchUserLocation(),
    );
    notifyListeners();
  }

  void stopTracking() {
    _isTrackingEnabled = false;
    _locationTimer?.cancel();
    _locationTimer = null;
    _userLocation = null;
    notifyListeners();
  }

  Future<void> _fetchUserLocation() async {
    if (_isLocationLoading || _currentBuildingId == null || _currentFloor == null) return;

    _isLocationLoading = true;
    notifyListeners();

    try {
      final featureVector = await _wifiService.scanFeatureVector();
      debugPrint('Feature vector: $featureVector');

      final coords = await _positioningService.getCurrentLocation(
        Constants.getUserLocation,
        _currentBuildingId!,
        _currentFloor!,
        featureVector,
        "session_id"
      );

      if (coords != null) {
        _userLocation = coords;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Error fetching user location: $e');
    } finally {
      _isLocationLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchUserLocationManual({
    required int buildingId,
    required int selectedFloor,
  }) async {
    // Update context
    setContext(buildingId: buildingId, floor: selectedFloor);

    // Fetch location immediately
    return _fetchUserLocation();
  }

  void clearLocation() {
    _userLocation = null;
    notifyListeners();
  }

  // Update context when floor changes
  void updateFloor(int newFloor) {
    _currentFloor = newFloor;
    clearLocation(); // Clear old location when floor changes
  }

  @override
  void dispose() {
    stopTracking();
    super.dispose();
  }
}