import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import 'package:http/http.dart' as http;
import 'package:indigo_test/constants.dart';
import '../../models/Building.dart';

class HomeService {

  Future<List<Building>> getAllBuildings() async {
    final url = Uri.parse(Constants.getAllBuildingsNames); // Replace with your actual endpoint

    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final List<dynamic> jsonList = jsonDecode(response.body);

          final buildings = jsonList.map<Building>((item) {
          final id = item['id'] ?? 0;
          final name = item['name'] ?? 'Building $id';
          final city = item['city'] ?? '';
          final street = item['address'] ?? '';
          final floorList = (item['floors'] as List<dynamic>).map<int>((f) => f as int).toList();


          return Building(
            buildingId: id,
            name: name,
            city: city,
            address: street, // Combine street and city for address
          );
        }).toList();

        return buildings;
      } else {
        throw Exception('Failed to load buildings: ${response.statusCode}');
      }
    } catch (e) {
      print('Error in getAllBuildings: $e');
      rethrow;
    }
  }

  /// Fetches the SVG file **THAT THE CLIENT GETS** from a URL and caches it using DefaultCacheManager.
  static Future<Uint8List?> loadUserSvgWithCache(int buildingId, int floor) async {
    final svgUrl = "https://your-api.com/buildings/$buildingId?floor=$floor"; // Replace with your actual URL;
    try {
      final file = await DefaultCacheManager().getSingleFile(svgUrl);
      return await file.readAsBytes();
    } catch (e) {
      print('Error caching SVG: $e');
      return null;
    }
  }
}