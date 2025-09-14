import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/navigation_data.dart';
import '../general.dart';
import '../../constants.dart';

class NavigationService extends ChangeNotifier {
  static final NavigationService _instance = NavigationService._internal();
  factory NavigationService() => _instance;
  NavigationService._internal();

  final GeneralService _generalService = GeneralService();

  bool _isRouteLoading = false;
  NavigationData? _currentNavigation;
  String? _routeSvgData;

  // Getters
  bool get isRouteLoading => _isRouteLoading;
  NavigationData? get currentNavigation => _currentNavigation;
  String? get routeSvgData => _routeSvgData;

  Future<String?> fetchRoute({
    required int buildingId,
    required int floorId,
    required String start,
    required String goal,
  }) async {
    if (start.isEmpty || goal.isEmpty) {
      throw ArgumentError('Start and goal cannot be empty');
    }

    _isRouteLoading = true;
    notifyListeners();

    try {
      final url = Uri.parse(Constants.getRoute);
      final svgData = await _generalService.sendSvgRequest(
        url: url,
        method: "GET",
        queryParams: {
          'buildingId': buildingId.toString(),
          'floorId': floorId.toString(),
          'start': start,
          'goal': goal,
        },
      );

      _routeSvgData = svgData;
      _currentNavigation = NavigationData(
        destination: goal,
        currentLocation: start,
      );

      return svgData;
    } on TimeoutException {
      throw Exception('The routing request timed out. Please try again.');
    } catch (e) {
      throw Exception('Failed to fetch route: $e');
    } finally {
      _isRouteLoading = false;
      notifyListeners();
    }
  }

  void clearRoute() {
    _routeSvgData = null;
    _currentNavigation = null;
    notifyListeners();
  }
}