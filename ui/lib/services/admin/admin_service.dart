import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import 'package:http/http.dart' as http;
import 'package:indigo_test/constants.dart';
import 'package:indigo_test/models/Building.dart';
import 'package:http_parser/http_parser.dart';
import '../../models/Room.dart';
import '../user/home_screen_service.dart'; // For MediaType


class AdminService {

  /// This methods get the building list that the admin owns.
  Future<List<Building>> getUserBuildings() async {
    return await HomeService().getAllBuildings();
  }

  static Future<String> uploadDxfAndYaml({required String fileName ,required int buildingId ,required int floorId ,required Uint8List fileBytes, required String yaml,}) async
  {
    try{
      final uri = Uri.parse(Constants.newFloor);

      final request = http.MultipartRequest('POST', uri)
        ..files.add(http.MultipartFile.fromBytes(
          'dwg',
          fileBytes,
          filename: fileName,
          contentType: MediaType('application', 'octet-stream'),
        ))
        ..files.add(http.MultipartFile.fromString(
          'yaml',
          yaml,
          filename: 'config.yaml',
          contentType: MediaType('text', 'plain'),
        ))
        ..fields['floorId'] = floorId.toString()
        ..fields['buildingId'] = buildingId.toString();

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();
      final contentType = response.headers['content-type'] ?? '';

      if (response.statusCode == 200) {
        if (contentType.contains('image/svg+xml') || contentType.contains('text/xml')) {
          return responseBody; // raw SVG
        } else {
          final jsonData = json.decode(responseBody);
          if (jsonData.containsKey('svg_data')) {
            return jsonData['svg_data'] as String;
          } else if (jsonData.containsKey('data')) {
            return jsonData['data'] as String;
          } else {
            throw Exception('Invalid response format: SVG data not found');
          }
        }
      } else if (response.statusCode == 404) {
        throw Exception('SVG file not found for building ID: 4');
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized: Please check your authentication');
      } else if (response.statusCode == 403) {
        throw Exception('Forbidden: You don\'t have permission to access this resource');
      } else {
        throw Exception('Failed to load SVG: ${response.statusCode} - ${response.reasonPhrase}');
      }
    } catch (e) {
      print('Error in uploadDxfAndYaml: $e');
      if (e.toString().contains('SocketException') || e.toString().contains('Connection')) {
        throw Exception('Network error: Please check your internet connection');
      }
      rethrow;
    }

  }

   static Future<void> updateRoomNames({
    required int buildingId,
    required int floorId,
    required List<Room> rooms,
    }) async {
    final url = Uri.parse(Constants.updateDoorsName); // Define this constant
    final body = {
      'buildingID': buildingId,
      'floorId': floorId,
      'doors': {
        for (var room in rooms)
          room.id.toString(): room.name ?? '',
      },
    };


    final response = await http.put(url,
      headers: {'Content-Type': 'application/json',},
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to update room names: ${response.body}');
    }
  }




  /// Fetches the SVG file **THAT THE ADMIN GETS** and can manage the labels and add nodes.
  static Future<Uint8List?> loadAdminSvgWithCache(int buildingId, int floorNumber) async {
    //final svgUrl = "http://your-api.com/buildings/$buildingId" ;
    final svgUrl = "https://www.svgrepo.com/download/533811/donuts-cake.svg" ;
    try {
      final file = await DefaultCacheManager().getSingleFile(svgUrl);
      return await file.readAsBytes();
    } catch (e) {
      print('Error caching SVG: $e');
      return null;
    }
  }
}