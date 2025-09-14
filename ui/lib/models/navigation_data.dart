class NavigationData {
  final String? destination;
  final String? currentLocation;
  final List<String>? route;
  final double? distanceToDestination;

  const NavigationData({
    this.destination,
    this.currentLocation,
    this.route,
    this.distanceToDestination,
  });

  Map<String, dynamic> toJson() {
    return {
      if (destination != null) 'destination': destination,
      if (currentLocation != null) 'currentLocation': currentLocation,
      if (route != null) 'route': route,
      if (distanceToDestination != null) 'distanceToDestination': distanceToDestination,
    };
  }

  factory NavigationData.fromJson(Map<String, dynamic> json) {
    return NavigationData(
      destination: json['destination'],
      currentLocation: json['currentLocation'],
      route: json['route']?.cast<String>(),
      distanceToDestination: json['distanceToDestination']?.toDouble(),
    );
  }
}