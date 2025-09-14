class UserLocation {
  final double x;
  final double y;
  final int? floor;
  final double? confidence;
  final int? label;

  const UserLocation({
    required this.x,
    required this.y,
    this.floor,
    this.confidence,
    this.label
  });

  UserLocation copyWith({
    double? x,
    double? y,
    int? floor,
    double? confidence,
  }) {
    return UserLocation(
      x: x ?? this.x,
      y: y ?? this.y,
      floor: floor ?? this.floor,
      confidence: confidence ?? this.confidence,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'svgX': x,
      'svgY': y,
    };
  }
  @override
  String toString() {
    return '$x,$y';
  }

  factory UserLocation.fromJson(Map<String, dynamic> json) {
    return UserLocation(
      x: (json['svgX'] as num).toDouble(),
      y: (json['svgY'] as num).toDouble(),
      //label: json['label'] as int?,
    );
  }

}