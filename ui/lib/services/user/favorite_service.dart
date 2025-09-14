import 'dart:convert';
import 'package:http/http.dart' as http;

import '../../constants.dart';
import '../../models/Building.dart';


class FavoriteService {

  // Add building to favorites
  Future<bool> addToFavorites(int buildingId) async {
    return true;
    try {
      final url = Uri.parse('${Constants.baseUrl}/favorites/add'); // Update with your actual endpoint
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          // Add authorization headers if needed
          // 'Authorization': 'Bearer ${your_token}',
        },
        body: jsonEncode({
          'buildingId': buildingId,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return true;
      } else {
        throw Exception('Failed to add to favorites: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error adding to favorites: $e');
    }
  }

  // Remove building from favorites
  Future<bool> removeFromFavorites(int buildingId) async {
    return true;
    try {
      final url = Uri.parse('${Constants.baseUrl}/favorites/remove'); // Update with your actual endpoint
      final response = await http.delete(
        url,
        headers: {
          'Content-Type': 'application/json',
          // Add authorization headers if needed
          // 'Authorization': 'Bearer ${your_token}',
        },
        body: jsonEncode({
          'buildingId': buildingId,
        }),
      );

      if (response.statusCode == 200 || response.statusCode == 204) {
        return true;
      } else {
        throw Exception('Failed to remove from favorites: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error removing from favorites: $e');
    }
  }

  // Toggle favorite status
  Future<bool> toggleFavorite(Building building, bool isFavorite) async {
    if (isFavorite) {
      return await addToFavorites(building.buildingId);
    } else {
      return await removeFromFavorites(building.buildingId);
    }
  }

  // Get user's favorite buildings
  Future<List<Building>> getFavoriteBuildings() async {
    return [];
    try {
      final url = Uri.parse('${Constants.baseUrl}/favorites'); // Update with your actual endpoint
      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json',
          // Add authorization headers if needed
          // 'Authorization': 'Bearer ${your_token}',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((json) => Building.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load favorite buildings: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error loading favorite buildings: $e');
    }
  }
}