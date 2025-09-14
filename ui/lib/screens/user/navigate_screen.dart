import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:flutter_compass/flutter_compass.dart';
import 'package:indigo_test/constants.dart';
import 'package:indigo_test/models/Building.dart';
import 'package:indigo_test/services/general.dart';
import 'package:indigo_test/services/admin/positioning_service.dart';
import 'package:indigo_test/services/dataCollection/wifi_positioning_service.dart';
import 'package:indigo_test/widgets/floor_picker.dart';
import 'package:indigo_test/widgets/navigation_bottom_sheet.dart';

import '../../models/user_location.dart';
import '../../widgets/dialogs/error_dialog.dart';
import '../../widgets/map/svg_map_with_location.dart';
import '../../utils/svg_parser.dart';

import 'package:android_id/android_id.dart';
import '../../widgets/dialogs/arrival_dialog.dart'; // showArrivalDialog(...)
import '../../widgets/no_floors_in_building.dart'; // showArrivalDialog(...)





class UserFloorView extends StatefulWidget {
  final Building building;
  const UserFloorView({Key? key, required this.building}) : super(key: key);

  @override
  State<UserFloorView> createState() => _UserFloorViewState();
}

class _UserFloorViewState extends State<UserFloorView> {
  int selectedFloor = 1;
  String? svgData;
  List<int> floorsList = [];
  List<String> places = [];

  double svgWidth = 800;
  double svgHeight = 800;

  final GeneralService generalService = GeneralService();
  final WifiPositioningService wifiService = WifiPositioningService.instance;
  final PositioningService positioningService = PositioningService();

  UserLocation? userLocation;
  Timer? locationTimer;
  bool isLocationLoading = false;
  bool isRouteLoading = false;

  bool isTrackingEnabled = false;

  // PDR State - now integrated with location tracking
  bool isPdrRunning = false;
  double pdrNorthOffset = 14.0; // degrees to align SVG north with magnetic north
  double? headingDeg;
  int pdrSteps = 0;
  double stepLengthMeters = 0.55;
  final int minStepIntervalMs = 250;
  int _lastStepMs = 0;

  // PDR sensor subscriptions
  StreamSubscription? _accSub;
  StreamSubscription? _compassSub;
  double _emaMag = 0.0;
  final double _smoothAlpha = 0.2;
  final double _stepThreshold = 1.2;
  double _prevEmaMag = 0.0;

  // PDR coordinate conversion (meters to SVG pixels)
  double metersToPixelScale = 8.5; // 8.5 pixels per meter (adjustable)

  bool isNavigating = true;       // true when a route SVG is shown
  bool isLiveLocationOn = false;
  final _androidIdPlugin = AndroidId();
  String? sessionID;

  var currentPath = <UserLocation>[];
  bool isFloorsLoading = true;
  bool _arrivalShownForCurrentRoute = false;


  @override
  void initState(){
    super.initState();
    _loadFloorsAndData();
  }

  @override
  void dispose() {
    locationTimer?.cancel();
    _stopPdr();
    super.dispose();
  }

  Future<void> _initAsync() async {
    try {
      await wifiService.init(); // <-- use this if your init() has no parameters
    } catch (e) {
      debugPrint('Init error: $e');
      if (!mounted) return;
      // If you want to notify the user, schedule after frame:
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Initialization failed: can\'t use location tracking on your current network')),
        );
      });
    }
  }

  Future<void> _startLocationTracking() async {
    locationTimer?.cancel();
    locationTimer = Timer.periodic(const Duration(seconds: 12), (_) async {
      if (!mounted || !isTrackingEnabled) return;
      if (isNavigating  && isPdrRunning) {
        if (!isLocationLoading) {
          setState(() => isLocationLoading = true);
          try {
            print("Fetching estimated location from server...");
            await getEstimatedLocation();
          } finally {
            if (mounted) setState(() => isLocationLoading = false);
          }
        }
      }
    });
  }

  Future<void> _startPdr() async {
    // Ensure we have a location before starting PDR
    if (userLocation == null) {
      await fetchUserStartPosition().then((_) {
        if (userLocation != null) {
          _startPdrSensors();
        }
      });
    } else {
      _startPdrSensors();
    }
  }

  void _startPdrSensors() {
    int timer = 0 ;
    isPdrRunning = true;

    // Start compass
    _compassSub = FlutterCompass.events?.listen((event) {
      setState(() {
        headingDeg = event.heading;
      });
    });

    // Start accelerometer
    _accSub = userAccelerometerEventStream().listen((e) {
      final nowMs = DateTime.now().millisecondsSinceEpoch;
      final mag = sqrt(e.x * e.x + e.y * e.y + e.z * e.z);

      _emaMag = (1 - _smoothAlpha) * _emaMag + _smoothAlpha * mag;

      final bool rising = _prevEmaMag <= _stepThreshold && _emaMag > _stepThreshold;
      final bool spaced = (nowMs - _lastStepMs) > minStepIntervalMs;

      if (rising && spaced) {
        _lastStepMs = nowMs;
        pdrSteps += 1;

        if (userLocation != null) {
          // Convert current SVG coordinates back to meters for calculation
          final currentMeterX = (userLocation!.x - svgWidth / 2) / metersToPixelScale;
          final currentMeterY = (svgHeight / 2 - userLocation!.y) / metersToPixelScale;

          // Calculate movement with north offset compensation
          final double adjustedHeading = ((headingDeg ?? 0.0) + pdrNorthOffset) * pi / 180.0;
          final newMeterX = currentMeterX + stepLengthMeters * sin(adjustedHeading);
          final newMeterY = currentMeterY + stepLengthMeters * cos(adjustedHeading);

          // Convert back to SVG coordinates
          final svgX = (svgWidth / 2) + (newMeterX * metersToPixelScale);
          final svgY = (svgHeight / 2) - (newMeterY * metersToPixelScale); // SVG Y is inverted

          setState(() {
            final predPDR = UserLocation(x: svgX, y: svgY);
            if (timer % 3 == 0) {
              userLocation = _pathCoordinateCorrection(predPDR);
            }else {
              userLocation = predPDR;
            }
            _checkArrivalAndMaybeShow();
            final loc = userLocation;
            if (loc == null) return;
            //debug
            print('PDR updated to ${loc.x}, ${loc.y}');
            timer++;
          });
        }
      }

      _prevEmaMag = _emaMag;
    });

    setState(() {
      timer++;
    });
  }

  UserLocation _pathCoordinateCorrection(UserLocation p) {
    if (currentPath.isEmpty) return UserLocation(x: -1, y: -1);

    UserLocation? best;
    double bestDist2 = double.infinity;

    for (final point in currentPath) {
      final dx = point.x - p.x;
      final dy = point.y - p.y;
      final d2 = dx * dx + dy * dy;

      if (d2 < bestDist2) {
        bestDist2 = d2;
        best = point;               // <-- corrected: use point, not p
      }
    }
    return best ?? UserLocation(x: -1, y: -1);
  }

  void _stopPdr() {
    isPdrRunning = false;
    _accSub?.cancel();
    _accSub = null;
    _compassSub?.cancel();
    _compassSub = null;
    setState(() {});
  }

  void _resetPdr({bool calledFromToggle = false}) {
    pdrSteps = 0;
    _lastStepMs = 0;
    _emaMag = 0;
    _prevEmaMag = 0;

    // Only fetch here if we explicitly want a fresh anchor and we're not in the middle of the toggle flow
    // (The toggle already awaited a fresh position)
    if (!calledFromToggle && isTrackingEnabled) {
      fetchUserStartPosition();
    }
  }

  // Helper method to get current position in meters for display
  String _getCurrentPositionInMeters() {
    if (userLocation == null) return "0.0m, 0.0m";

    final meterX = (userLocation!.x - svgWidth / 2) / metersToPixelScale;
    final meterY = (svgHeight / 2 - userLocation!.y) / metersToPixelScale;

    return "${meterX.toStringAsFixed(1)}m, ${meterY.toStringAsFixed(1)}m";
  }

  void _toggleNavigationMode() async {
    final turningOn = !isLiveLocationOn;

    setState(() {
      isLiveLocationOn = turningOn;

      if (isLiveLocationOn) {
        // ensure the chooser contains a "Current Location" option once
        if (!places.contains('Current Location')) {
          places.insert(0, 'Current Location');
        }
        isTrackingEnabled = true;   // make sure tracking flag is on
      } else {
        // turning OFF
        _startStopNavigationFromCurrentLocation();
        isTrackingEnabled = false;
        isPdrRunning = false;
        if (places.contains('Current Location')) {
          places.remove('Current Location');
        }
      }
    });

    if (isLiveLocationOn) {
      await _initAsync();
      await fetchUserStartPosition();
    }
  }

  void _startStopNavigationFromCurrentLocation() async {
    if (isLiveLocationOn) {
      // turn ON: enable tracking + start PDR
      if (!isTrackingEnabled) {
        setState(() => isTrackingEnabled = true);
      }
      //TODO debug mute server correction
      //await _startLocationTracking();   // server correction loop
      _resetPdr(calledFromToggle: true);
      await _startPdr();                // start sensors
    } else {
      // turn OFF: stop everything
      locationTimer?.cancel();
      _stopPdr();
      setState(() {
        isTrackingEnabled = false;
        isPdrRunning = false;
        userLocation = null; // or keep last point

      });
    }
  }

  Future<void> fetchUserStartPosition() async {
    if (isLocationLoading) return;

    setState(() => isLocationLoading = true);

    try {
      final featureVector = await wifiService.scanFeatureVector();
      final coords = await positioningService.getCurrentLocation(
        Constants.getUserLocation,
        widget.building.buildingId,
        selectedFloor,
        featureVector,
        sessionID ?? "unknown_session",
      );


      if (coords != null && mounted) {
        setState(() => userLocation = coords);
      }
    } catch (e) {
      debugPrint('Error fetching user location: $e');
    } finally {
      if (mounted) setState(() => isLocationLoading = false);
    }
  }

  Future<void> getEstimatedLocation() async {
    if (userLocation == null) return;
    try {
      final featureVector = await wifiService.scanFeatureVector();
      final coords = await positioningService.getEstimatedLocation(
        Constants.getEstimatedLocation,
        widget.building.buildingId,
        selectedFloor,
        featureVector,
        userLocation!,
        sessionID ?? "unknown_session",
      );
      if (coords != null && mounted) {
        setState(() => userLocation = coords);
        _checkArrivalAndMaybeShow();

        //debug
        final loc = userLocation;
        if (loc == null) return;
        print('the server update to ${loc.x}, ${loc.y}');
      }
    } catch (e) {
      debugPrint('Error fetching estimated location: $e');
    } finally {
      if (mounted) setState(() => isLocationLoading = false);
    }
  }

  Future<void> _loadFloorsAndData() async {
    try {
      if (mounted) setState(() => isFloorsLoading = true);

      final list = await generalService.getFloors(
        buildingId: widget.building.buildingId,
      );
      if (!mounted) return;

      setState(() {
        floorsList = list;
        if (list.isNotEmpty) selectedFloor = list.first;
      });

      if (floorsList.isEmpty) {
        _stopPdr();
        if (mounted) setState(() => isFloorsLoading = false);
        return;
      }
      await _loadSvg();
      await _loadRoomNames();
      await _loadOneCmSvg();
      await _initSessionId();

    } catch (e) {
      debugPrint('Error loading floors: $e');
    } finally {
      if (mounted) setState(() => isFloorsLoading = false);
    }
  }

  Future<void> _loadSvg() async {
    final url = Uri.parse(Constants.getFloorSvg);
    svgData = await generalService.sendSvgRequest(
      url: url,
      method: "GET",
      queryParams: {
        'buildingId': widget.building.buildingId.toString(),
        'floorId': selectedFloor.toString(),
      },
    );

    if (svgData != null) {
      final dims = SvgParser.parseDimensions(svgData!);
      svgWidth = dims.width;
      svgHeight = dims.height;
    }

    if (mounted) setState(() {});
  }

  Future<void> _loadRoomNames() async {
    try {
      final url = Uri.parse(Constants.getDoorsName);
      places = await generalService.fetchRoomsNameFromFloor(
        url: url,
        queryParams: {
          'buildingId': widget.building.buildingId.toString(),
          'floorId': selectedFloor.toString(),
        },
      );
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint('Error loading room names: $e');
    }
  }

  Future<void> _loadOneCmSvg() async {
    try {
      final floorData = await positioningService.fetchOneCmSvg(
        widget.building.buildingId,
        selectedFloor,
      );

      if (!mounted) return;

      setState(() {
        if (floorData != null) {
          // If pixelToM is meters per pixel → cm per pixel = m/px * 100
          final mPerPx = floorData.pixelToM;
          metersToPixelScale = (mPerPx != null) ? (mPerPx * 100.0) : 8.5;

          pdrNorthOffset = floorData.northOffset ?? 14.0;
        } else {
          // Whole object missing → hard defaults
          metersToPixelScale = 8.5;
          pdrNorthOffset = 14.0;
        }
      });
    } catch (e) {
      debugPrint('Error loading floor data: $e');
      if (!mounted) return;
      setState(() {
        metersToPixelScale = 8.5;
        pdrNorthOffset = 14.0;
      });
    }
  }

  Future<void> _initSessionId() async {
    try {
      sessionID = await _androidIdPlugin.getId(); // this works
      // or: String? sessionID = await _androidIdPlugin.androidId;
      print("Device session ID: $sessionID");
    } catch (e) {
      print("Error reading ANDROID_ID: $e");
    }
  }

  Future<void> getNavigationRoute(Map<String, dynamic> nav) async {
    final curr = nav['currentLocation'] as String?;
    final dest = nav['destination'] as String?;
    if (dest == null || curr == null || dest.isEmpty || curr.isEmpty) return;

    if (!mounted) return;
    setState(() {
      isNavigating = true;
      isRouteLoading = true;
      svgData = null;
      _arrivalShownForCurrentRoute = false;
    });

    String? newSvg;
    String? errorText;

    try {
      final url = Uri.parse(Constants.getRoute);
      newSvg = await generalService.sendSvgRequest(
        url: url,
        method: "GET",
        queryParams: {
          'buildingId': widget.building.buildingId.toString(),
          'floorId': selectedFloor.toString(),
          'sessionId': sessionID ?? "unknown_session",
          'start':curr,
          'goal': dest,
          'coordinate': userLocation.toString(),
        },
      ).timeout(const Duration(seconds: 60));
    } on TimeoutException {
      errorText = 'The routing request timed out. Please try again.';
    } catch (e) {
      errorText = 'Failed to fetch route: $e';
    }

    if (!mounted) return;

    if (errorText != null) {
      await ErrorDialog.show(context, errorText);
      await _loadSvg();
    } else {
      final dims = SvgParser.parseDimensions(newSvg!);
      if(isLiveLocationOn){
        _startStopNavigationFromCurrentLocation();
      }
      svgWidth = dims.width;
      svgHeight = dims.height;
      setState(() {
        userLocation = currentPath.isNotEmpty && isLiveLocationOn ? currentPath.first : userLocation;
        svgData = newSvg;
      });
    }

    if (mounted) {
      setState(() => isRouteLoading = false);
    }
  }

  Future<void> getRoutePoints(Map<String, dynamic> nav) async {
    final curr = nav['currentLocation'] as String?;
    final dest = nav['destination'] as String?;
    if (curr == null || dest == null || curr.isEmpty || dest.isEmpty) {
      if (!mounted) return;
      setState((){
        currentPath = <UserLocation>[];
        _arrivalShownForCurrentRoute = false;
      });
      return;
    }

    try {
      final url = Uri.parse(Constants.getRoutePoints);

      final resp = await generalService
          .sendRequest(
        url: url,
        method: "GET",
        queryParams: {
          'buildingId': widget.building.buildingId.toString(),
          'floorId': selectedFloor.toString(),
          'sessionId': sessionID ?? "unknown_session",
          'start': curr,
          'goal': dest,
          'coordinate': userLocation.toString(),
        },
      )
          .timeout(const Duration(seconds: 60));

      if (resp is! Map<String, dynamic>) {
        throw Exception("Unexpected response type: ${resp.runtimeType}");
      }

      final dynamic pathDyn = resp['path'];
      if (pathDyn is! List) {
        throw Exception("Missing/invalid 'path' array in response");
      }

      final points = <UserLocation>[];
      for (final p in pathDyn) {
        if (p is List && p.length >= 2 && p[0] is num && p[1] is num) {
          points.add(
            UserLocation(
              x: (p[0] as num).toDouble(),
              y: (p[1] as num).toDouble(),
              floor: selectedFloor,
            ),
          );
        }
      }

      if (!mounted) return;
      setState(() {
        currentPath = points; // <-- store result here
      });
    } on TimeoutException {
      if (!mounted) return;
      setState(() => currentPath = <UserLocation>[]);
      throw Exception("Navigation points request timed out.");
    } catch (e) {
      if (!mounted) return;
      setState(() => currentPath = <UserLocation>[]);
      throw Exception("Failed to fetch navigation points: $e");
    }
  }

  double _distancePx(UserLocation a, UserLocation b) {
    final dx = a.x - b.x;
    final dy = a.y - b.y;
    return sqrt(dx*dx + dy*dy);
  }

  double _metersToPixels(double meters) {
    // metersToPixelScale is px-per-meter in your code (you divide px by it to get meters).
    // If you ever switch to meters-per-pixel, change to: return meters / metersToPixelScale;
    return meters * metersToPixelScale;
  }

  Future<void> _checkArrivalAndMaybeShow() async {
    if (_arrivalShownForCurrentRoute) return;
    if (!isNavigating) return;
    if (userLocation == null) return;
    if (currentPath.isEmpty) return;

    final lastPoint = currentPath.last;
    final distPx = _distancePx(userLocation!, lastPoint);
    final thresholdPx = _metersToPixels(1.0); // 0.5 meters

    if (distPx <= thresholdPx) {
      _arrivalShownForCurrentRoute = true;

      if (!mounted) return;
      await showArrivalDialog(
        context,
        destinationName: "Destination",
        subtitle: "You’re arrive to the goal. Nice!",
        primaryText: "Finish",
        onPrimary: () {
          // e.g., clean up UI
          _stopPdr();
          setState(() {
            isNavigating = false;
            isLiveLocationOn = false;
            userLocation = null;
          });
          _loadSvg();
        },
        secondaryText: "Keep Exploring",
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.building.name),
        centerTitle: true,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (isLiveLocationOn)
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 20),
                    tooltip: 'Align North',
                    onPressed: _resetPdr,
                  ),
                // Single master toggle: Navigation (starts/stops tracking + PDR)
                IconButton(
                  icon: Icon(
                    isLiveLocationOn ? Icons.navigation : Icons.navigation_outlined,
                    color: isLiveLocationOn ? Colors.blue : Colors.grey,
                    size: 20,
                  ),
                  tooltip: 'Navigation',
                  onPressed: _toggleNavigationMode,
                ),
              ],
            ),
          ),
        ],
      ),
      body: isFloorsLoading
          ? const Center(
        child: CircularProgressIndicator(),
      )
          : floorsList.isEmpty
          ? buildEmptyState()
          : Stack(
        children: [
          Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    FloorPickerButton(
                      floorsList: floorsList,
                      selectedFloor: selectedFloor,
                      onFloorSelected: (floor) {
                        setState(() {
                          selectedFloor = floor;
                          isNavigating = false;
                          isLiveLocationOn = false;
                          isTrackingEnabled = false;
                          _startStopNavigationFromCurrentLocation();
                        });
                        _loadSvg();
                        _loadRoomNames();
                        _loadOneCmSvg();

                        if (isPdrRunning) {
                          _resetPdr();
                        } else if (isTrackingEnabled) {
                          fetchUserStartPosition();
                        }
                      },
                    ),

                    // PDR info (kept as-is; shows when PDR is running)
                    if (isPdrRunning) ...[
                      const SizedBox(width: 16),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.green.shade50,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.green.shade200),
                          ),
                          child: Text(
                            'PDR: $pdrSteps steps | ${_getCurrentPositionInMeters()}',
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.refresh, size: 20),
                        tooltip: 'Reset PDR',
                        onPressed: _resetPdr,
                      ),
                    ],
                  ],
                ),
              ),

              Expanded(
                child: Padding(
                  padding: EdgeInsets.only(
                    bottom: MediaQuery.of(context).size.height * 0.15,
                  ),
                  child: svgData == null
                      ? const Center(child: CircularProgressIndicator())
                      : SvgMapWithLocation(
                    svgData: svgData!,
                    userLocation: userLocation,
                    svgWidth: svgWidth,
                    svgHeight: svgHeight,
                  ),
                ),
              ),
            ],
          ),

          Align(
            alignment: Alignment.bottomCenter,
            child: NavigationBottomSheet(
              //onNavigationPressed: getNavigationRoute,
              onNavigationPressed: (nav) async {
                try {
                  await getRoutePoints(nav);
                  await getNavigationRoute(nav);
                  print("after function $currentPath");
                } catch (e) {
                  if (!mounted) return;
                  await ErrorDialog.show(context, 'Failed to load route points: $e');
                }
              },
              places: places,
            ),
          ),
        ],
      ),
    );
  }

}