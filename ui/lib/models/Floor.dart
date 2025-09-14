import 'Building.dart';

class Floor{
  int id;
  String name;
  Building? building;

  Floor({
    required this.id,
    required this.name,
    this.building,
  });

  int get buildingId {
    return building?.buildingId ?? 0; // Return 0 if building is null
  }
  String get buildingName {
    return building?.name ?? 'Unknown'; // Return 'Unknown' if building is null
  }

}