class Building {
  final int buildingId;
  final String name;
  final String city;
  final String address;
  final List<String> floorList = [];
  int numberOfFloors = 0;

  bool isFavorite; // Add this line

  Building({
    required this.buildingId,
    required this.name,
    required this.city,
    required this.address,

    this.isFavorite = false, // Add this with default value
  });

  // Update your fromJson factory method to include isFavorite
  factory Building.fromJson(Map<String, dynamic> json) {
    return Building(
      buildingId: json['buildingId'],
      name: json['name'],
      city: json['city'],
      address: json['address'],

      isFavorite: json['isFavorite'] ?? false, // Add this line
    );
  }

  // Update your toJson method to include isFavorite
  Map<String, dynamic> toJson() {
    return {
      'buildingId': buildingId,
      'name': name,
      'city': city,
      'address': address,
      'floorList': floorList,

      'isFavorite': isFavorite, // Add this line
    };
  }
}