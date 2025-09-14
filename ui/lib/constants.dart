class Constants {
  // Global constants
  static const String lineSeparator = '\n'; // Dart does not use System.getProperty

  static const int refreshRate = 500;

  // Server resources locations
  static const String baseDomain = "indoor-navigation-server.onrender.com";
  static const String port = "8574";

  static const String baseUrl = "https://$baseDomain";
  static const String contextPath = "/IndiGo";
  static const String fullServerPath = baseUrl;


  // API Endpoints
  static const String newFloor = "$fullServerPath/floor/add";
  static const String newBuilding = "$fullServerPath/building/add";
  static const String getAllFloorsInBuilding = "$fullServerPath/building/getFloors";
  static const String getAllBuildingsNames = "$fullServerPath/building/get";
  static const String getFloorSvg = "$fullServerPath/floor/getSvgDirect";
  static const String getDoorsName = "$fullServerPath/floor/getDoors";
  static const String updateDoorsName = "$fullServerPath/floor/updateDoorsNames";
  static const String calibrateFloorPlan = "$fullServerPath/floor/calibrate";
  static const String getRoute = "$fullServerPath/floor/route/get";
  static const String getRoutePoints = "$fullServerPath/floor/getRouteList";
  static const String train = "$fullServerPath/floor/scan";
  static const String sendFingerprint = "$fullServerPath/floor/scan/upload";
  static const String getUserLocation = "$fullServerPath/predict/top1";
  static const String getEstimatedLocation = "$fullServerPath/predict/get";
  static const String getMetersToPixelScaleUri = "$fullServerPath/floor/getOneCmSvg";
  static const String getGridSvg = "$fullServerPath/floor/getGridSvg";

  static const Map<String, String> headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    // Add authentication headers if needed
    // 'Authorization': 'Bearer $token',
  };



}
