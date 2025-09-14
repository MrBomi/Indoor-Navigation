import 'dart:async';
import 'dart:io';

import 'package:permission_handler/permission_handler.dart';
import 'package:wifi_scan/wifi_scan.dart' as wscan;
import 'package:network_info_plus/network_info_plus.dart';
import 'package:geolocator/geolocator.dart';

class WifiPositioningService {
  WifiPositioningService._();
  static final WifiPositioningService instance = WifiPositioningService._();

  // Cached values
  Map<String, int>? lastFeatureVector;
  DateTime? lastScanAt;
  bool _initialized = false;

  // Throttle to avoid Android scan limits (typical system throttle ~ every 2-4s)
  Duration minScanInterval = const Duration(seconds: 1);

  /// Initialize:
  ///  - request needed permissions
  ///  - ensure Location Services are ON (required by Android for Wi-Fi scans)
  ///  - verify connected SSID equals [expectedSsid]
  Future<void> init() async {

    final okPerms = await ensurePermissions();
    if (!okPerms) {
      throw StateError('Wi-Fi permissions not granted');
    }

    final locOk = await ensureLocationServicesOn();
    if (!locOk) {
      throw StateError('Location Services must be ON for Wi-Fi scanning');
    }
    //TODO change for debugging(always true)
    //final ssidOk = await ensureCorrectNetwork();
    final ssidOk = true;

    if (!ssidOk) {
      final current = await getCurrentSsid();
      throw StateError(
        'Connected SSID "$current" does not match for this building.',
      );
    }

    // Optional: verify scanning capability
    final canScan = await wscan.WiFiScan.instance.canStartScan();
    if (canScan != wscan.CanStartScan.yes) {
      throw StateError('Device cannot start Wi-Fi scan: $canScan');
    }

    _initialized = true;
  }

  /// Request the necessary runtime permissions.
  /// Returns true if we have the set we need to scan Wi-Fi.
  Future<bool> ensurePermissions() async {
    if (!Platform.isAndroid) {
      // Best effort on non-Android (scanning typically unsupported)
      return false;
    }

    // Ask for both; on pre-13, NEARBY_WIFI_DEVICES is ignored by the OS.
    final statuses = await <Permission>[
      Permission.nearbyWifiDevices,   // Android 13+
      Permission.locationWhenInUse,   // required pre-13, still fine post-13
    ].request();

    final nearbyOk = statuses[Permission.nearbyWifiDevices]?.isGranted ?? true;
    final locOk = (statuses[Permission.locationWhenInUse]?.isGranted ?? false) ||
        (statuses[Permission.location]?.isGranted ?? false);

    return nearbyOk && locOk;
  }

  /// Ensure location services are turned ON (needed for Wi-Fi scanning).
  Future<bool> ensureLocationServicesOn() async {
    if (!Platform.isAndroid) return false;
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (enabled) return true;

    // Try to open settings; user action required
    await Geolocator.openLocationSettings();
    // Re-check after user returns
    return await Geolocator.isLocationServiceEnabled();
  }

  /// Returns sanitized current SSID (without quotes) or null.
  Future<String?> getCurrentSsid() async {
    try {
      final info = NetworkInfo();
      final ssid = await info.getWifiName(); // may return e.g. "\"MyWifi\""
      if (ssid == null) return null;
      return _stripQuotes(ssid.trim());
    } catch (_) {
      return null;
    }
  }

  /// Returns current BSSID (router MAC) or null.
  Future<String?> getCurrentBssid() async {
    try {
      final info = NetworkInfo();
      return await info.getWifiBSSID();
    } catch (_) {
      return null;
    }
  }

  /// Verifies the currently connected SSID matches [expectedSsid].
  Future<bool> ensureCorrectNetwork() async {
    final current = await getCurrentSsid();
    if (current == null) return false;

    final expectedSsid = "MTA WiFi"; // Replace with your building's SSID
    return _equalsSsid(current, expectedSsid);
  }

  /// Perform a Wi-Fi scan and build the feature vector:
  ///   { "bssid": rssi_dBm, ... }
  /// It also stores the result into [lastFeatureVector].
  /// [timeout] controls how long we wait for scan results to be ready.
  Future<Map<String, int>> scanFeatureVector({
    Duration timeout = const Duration(seconds: 2),
    int rssiFloor = -100,
  }) async {
    if (!_initialized) {
      throw StateError('Call init(expectedSsid: ...) before scanning.');
    }

    // // Throttle scans to respect platform restrictions.
    // if (lastScanAt != null && DateTime.now().difference(lastScanAt!) < minScanInterval) {
    //   // Return the last known result if we’re within throttle window.
    //   if (lastFeatureVector != null) return Map<String, int>.from(lastFeatureVector!);
    //   // Otherwise just wait a bit to avoid immediate scan spam.
    //   await Future<void>.delayed(minScanInterval);
    // }

    // Ensure capability
    final canStart = await wscan.WiFiScan.instance.canStartScan();
    if (canStart != wscan.CanStartScan.yes) {
      throw StateError('Cannot start Wi-Fi scan: $canStart');
    }

    // Start scan
    await wscan.WiFiScan.instance.startScan();

    // Get results (either wait a moment or use onScannedResultsAvailable stream).
    // Simple approach: small delay, then pull the latest snapshot.
    await Future<void>.delayed(timeout);

    final canGet = await wscan.WiFiScan.instance.canGetScannedResults();
    if (canGet != wscan.CanGetScannedResults.yes) {
      throw StateError('Cannot get scanned results: $canGet');
    }

    final List<wscan.WiFiAccessPoint> aps =
    await wscan.WiFiScan.instance.getScannedResults();

    final currentSsid = await getCurrentSsid();

    // Build vector
    final Map<String, int> vector = <String, int>{};

    for (final ap in aps) {
      final bssid = ap.bssid; // MAC
      if (bssid.isEmpty) continue;

      // filter only APs with the same SSID as the one we’re connected to
      final ssid = _stripQuotes(ap.ssid.trim());
      if (currentSsid == null || !_equalsSsid(ssid, currentSsid)) continue;


      // RSSI in dBm; clamp to floor (e.g., -100)
      final rssi = ap.level; // typically negative integer
      final clamped = rssi < rssiFloor ? rssiFloor : rssi;

      // If duplicate BSSID appears, keep the strongest (max dBm)
      if (!vector.containsKey(bssid) || clamped > (vector[bssid] ?? -999)) {
        vector[bssid] = clamped;
      }
    }

    lastFeatureVector = vector;
    lastScanAt = DateTime.now();
    return vector;
  }


  /// Last good vector or empty map.
  Map<String, int> get cachedVector => Map<String, int>.from(lastFeatureVector ?? const {});

  /// Utility to compare SSIDs case-insensitively (strip wrapping quotes if any).
  bool _equalsSsid(String a, String b) =>
      _stripQuotes(a).toLowerCase() == _stripQuotes(b).toLowerCase();

  String _stripQuotes(String s) {
    if (s.length >= 2 && s.startsWith('"') && s.endsWith('"')) {
      return s.substring(1, s.length - 1);
    }
    return s;
  }
}
