import 'Floor.dart';

class Room {
  final int id;
  final double x;
  final double y;
  String? name;
  Floor? floor;

  Room({required this.id, required this.x, required this.y, this.name, this.floor});

  int get floorId {
    return floor?.id ?? 0; // Return 0 if floor is null
  }

  String get floorName {
    return floor?.name ?? 'Unknown'; // Return 'Unknown' if floor is null
  }

  int get buildingId {
    return floor?.building?.buildingId ?? 0; // Return 0 if building is null
  }

  String get buildingName {
    return floor?.building?.name ?? 'Unknown'; // Return 'Unknown' if building is null
  }

  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['id'] as int,
      x: (json['scale_coord'][0] as num).toDouble(),
      y: (json['scale_coord'][1] as num).toDouble(),
      name: json['name'] as String?,
      floor: null, // Set this based on your needs
    );
  }
}