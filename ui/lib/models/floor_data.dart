class FloorData {
  final double? pixelToM;
  final double? northOffset;

  const FloorData({
    required this.pixelToM,
    required this.northOffset,
  });

  Map<String, dynamic> toJson() => {
    if (northOffset != null) 'north_offset': northOffset,
    if (pixelToM != null) 'one_cm_svg': pixelToM,
  };

  factory FloorData.fromJson(Map<String, dynamic> json) {
    final north = json.containsKey('north_offset')
        ? (json['north_offset'] as num?)?.toDouble()
        : null;

    final pxToM = json.containsKey('one_cm_svg')
        ? (json['one_cm_svg'] as num?)?.toDouble()
        : null;

    return FloorData(
      pixelToM: pxToM,
      northOffset: north,
    );
  }
}