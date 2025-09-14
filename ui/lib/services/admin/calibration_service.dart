import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../constants.dart';
import '../../models/Room.dart';

class CalibrationService {
  // TODO: Add your authentication headers if needed
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    // 'Authorization': 'Bearer your-token-here', // Add if needed
  };

  /// Loads SVG file for the specified building
  /// GET /buildings/{buildingId}/svg
  // Future<String> loadSvgFile(int buildingId) async {
  //   try {
  //     final url = Uri.parse('$_baseUrl/buildings/$buildingId/svg');
  //
  //     print('Loading SVG from: $url');
  //
  //     final response = await http.get(
  //       url,
  //       headers: _headers,
  //     ).timeout(
  //       const Duration(seconds: 30),
  //       onTimeout: () {
  //         throw Exception('Request timeout: Failed to load SVG file');
  //       },
  //     );
  //
  //     if (response.statusCode == 200) {
  //       // Check if response is SVG content
  //       final contentType = response.headers['content-type'] ?? '';
  //       if (contentType.contains('image/svg+xml') || contentType.contains('text/xml')) {
  //         return response.body;
  //       } else {
  //         // If response is JSON with SVG data
  //         final Map<String, dynamic> jsonData = json.decode(response.body);
  //         if (jsonData.containsKey('svg_data')) {
  //           return jsonData['svg_data'] as String;
  //         } else if (jsonData.containsKey('data')) {
  //           return jsonData['data'] as String;
  //         } else {
  //           throw Exception('Invalid response format: SVG data not found');
  //         }
  //       }
  //     } else if (response.statusCode == 404) {
  //       throw Exception('SVG file not found for building ID: $buildingId');
  //     } else if (response.statusCode == 401) {
  //       throw Exception('Unauthorized: Please check your authentication');
  //     } else if (response.statusCode == 403) {
  //       throw Exception('Forbidden: You don\'t have permission to access this resource');
  //     } else {
  //       throw Exception('Failed to load SVG: ${response.statusCode} - ${response.reasonPhrase}');
  //     }
  //   } catch (e) {
  //     print('Error in loadSvgFile: $e');
  //     if (e.toString().contains('SocketException') || e.toString().contains('Connection')) {
  //       throw Exception('Network error: Please check your internet connection');
  //     }
  //     rethrow;
  //   }
  // }

  /// Submits calibration data (two points and distance)
  /// POST /buildings/{buildingId}/calibration
  Future<List<Room>> submitCalibrationData({
    required int buildingId,
    required int buildingFloor,
    required Offset firstPoint,
    required Offset secondPoint,
    required double northOffset,
    required double distanceInCm,
  }) async {
    try {
      final url = Uri.parse(Constants.calibrateFloorPlan);

      // Calculate pixel distance for reference
      final pixelDistance = (secondPoint - firstPoint).distance;

      final requestBody = {
        'building_id': buildingId,
        'floor_id' : buildingFloor,
        'north_offset': northOffset,
        'calibration_data': {
          'first_point': {
            'x': firstPoint.dx,
            'y': firstPoint.dy,
          },
          'second_point': {
            'x': secondPoint.dx,
            'y': secondPoint.dy,
          },
          'real_distance_cm': distanceInCm,
          'pixel_distance': pixelDistance,
          'scale_factor': distanceInCm / pixelDistance, // cm per pixel
        },
      };

      print('Submitting calibration data to: $url');
      print('Request body: ${json.encode(requestBody)}');

      final response = await http.post(
        url,
        headers: _headers,
        body: json.encode(requestBody),
      ).timeout(
        const Duration(seconds: 120),
        onTimeout: () {
          throw Exception('Request timeout: Failed to submit calibration data');
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        print('Calibration data submitted successfully');
        return _parseUploadResponse(response.body);
      } else if (response.statusCode == 400) {
        final errorData = _parseErrorResponse(response.body);
        throw Exception('Bad request: ${errorData['message'] ?? 'Invalid calibration data'}');
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized: Please check your authentication');
      } else if (response.statusCode == 403) {
        throw Exception('Forbidden: You don\'t have permission to submit calibration data');
      } else if (response.statusCode == 404) {
        throw Exception('Building not found: ID $buildingId');
      } else if (response.statusCode == 422) {
        final errorData = _parseErrorResponse(response.body);
        throw Exception('Validation error: ${errorData['message'] ?? 'Invalid data format'}');
      } else {
        throw Exception('Failed to submit calibration: ${response.statusCode} - ${response.reasonPhrase}');
      }
    } catch (e) {
      print('Error in submitCalibrationData: $e');
      if (e.toString().contains('SocketException') || e.toString().contains('Connection')) {
        throw Exception('Network error: Please check your internet connection');
      }
      rethrow;
    }
  }

  List<Room> _parseUploadResponse(String body) {
    final json = jsonDecode(body);
    final doorsJson = json['doors'] as List;

    final doors = doorsJson.map((d) {
      return Room(
        id: d['id'],
        x: (d['x'] as num).toDouble(),
        y: (d['y'] as num).toDouble(),
      );
    }).toList();

    if (doors.isEmpty) {
      throw Exception('No doors found in the response');
    }

    if (json['buildingId'] == null) {
      throw Exception('Building ID not found in the response');
    }

    return doors;
  }


  /// Alternative method to load SVG with caching (similar to your AdminService pattern)
  /// This method can be used if you want to implement local caching
  // Future<Uint8List?> loadSvgWithCache(int buildingId) async {
  //   try {
  //
  //     final svgString = await loadSvgFile(buildingId);
  //     return Uint8List.fromList(utf8.encode(svgString));
  //   } catch (e) {
  //     print('Error in loadSvgWithCache: $e');
  //     return null;
  //   }
  // }

  /// Parses error response from server
  Map<String, dynamic> _parseErrorResponse(String responseBody) {
    try {
      return json.decode(responseBody) as Map<String, dynamic>;
    } catch (e) {
      return {'message': responseBody};
    }
  }

  /// Optional: Get calibration data for a building
  /// GET /buildings/{buildingId}/calibration
  // Future<Map<String, dynamic>?> getCalibrationData(int buildingId) async {
  //   try {
  //     final url = Uri.parse('$_baseUrl/buildings/$buildingId/calibration');
  //
  //     final response = await http.get(
  //       url,
  //       headers: _headers,
  //     ).timeout(const Duration(seconds: 15));
  //
  //     if (response.statusCode == 200) {
  //       return json.decode(response.body) as Map<String, dynamic>;
  //     } else if (response.statusCode == 404) {
  //       return null; // No calibration data found
  //     } else {
  //       throw Exception('Failed to get calibration data: ${response.statusCode}');
  //     }
  //   } catch (e) {
  //     print('Error in getCalibrationData: $e');
  //     return null;
  //   }
  // }

  /// Optional: Delete calibration data
  /// DELETE /buildings/{buildingId}/calibration
  // Future<bool> deleteCalibrationData(int buildingId) async {
  //   try {
  //     final url = Uri.parse('$_baseUrl/buildings/$buildingId/calibration');
  //
  //     final response = await http.delete(
  //       url,
  //       headers: _headers,
  //     ).timeout(const Duration(seconds: 15));
  //
  //     return response.statusCode == 200 || response.statusCode == 204;
  //   } catch (e) {
  //     print('Error in deleteCalibrationData: $e');
  //     return false;
  //   }
  // }
}