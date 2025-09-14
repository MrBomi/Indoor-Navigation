import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/cupertino.dart';
import 'package:http/http.dart' as http;
import 'package:indigo_test/constants.dart';
import 'package:indigo_test/models/floor_data.dart';
import '../../models/user_location.dart';
import 'package:http_parser/http_parser.dart' show MediaType;


class PositioningService {
  //For electromagnetic positioning
  Future<UserLocation?> sendElectromagnetData(String uri, int buildingId, int floorId, Map<String, Map<String, double>> data) async {
    try {
      final url = Uri.parse(uri);

      // Build point list
      final points = data.entries.map((e) => {
        'name': e.key,
        ...e.value,
      }).toList();

      // Final payload structure
      final payload = {
        'buildingId': buildingId,
        'floorId': floorId,
        'featureVector': points,
      };

      final response = await http.put(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      print('Server response: ${response.statusCode} ${response.body}');
      if(response.statusCode == 200 || response.statusCode == 201){
        final responseData = json.decode(response.body) as Map<String, dynamic>;
        if (response.statusCode == 200) {
          // Check if response contains coordinates
          if (responseData.containsKey('x') && responseData.containsKey('y')) {
            return UserLocation.fromJson(responseData);
          } else {
            print('Server response does not contain location coordinates');
            return null;
          }
        } else {
          //return UserLocation(x: 213.038, y: 319.85); // Auditorium for now. Indicating no location found
          return UserLocation(x: 213.038, y: 350.85); // Auditorium for now. Indicating no location found
        }
      } else {
        print('HTTP Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Network error in sendAll: $e');
      return null;
    }
  }

  //For WiFi positioning
  Future<bool> sendFingerprintCsvFile(String uri, File csvData, int buildingId,int floorId) async {
    try {
      final url = Uri.parse(uri);
      final bytes = await csvData.readAsBytes();

      final request = http.MultipartRequest('POST', url)
        ..fields.addAll({
          'floorId': floorId.toString(),
          'buildingId': buildingId.toString(),
        })
        ..files.add(
          http.MultipartFile.fromBytes(
            'scan',
            filename: "fingerprint.csv",
            bytes,
            contentType: MediaType('text', 'csv'),
          ),
        );

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      print('Server response: ${response.statusCode} ${response.body}');
      if (response.statusCode >= 200 && response.statusCode < 300) {
        print('Fingerprint data sent successfully.');
        return true;
      } else {
        print('HTTP Error: ${response.statusCode} - ${response.body}');
        return false;
      }
    } on TimeoutException {
      print('Network timeout in sendFingerprint');
      return false;
    } catch (e) {
      print('Network error in sendFingerprint: $e');
      return false;
    }
  }

  Future<UserLocation?> getCurrentLocation(String uri, int buildingId, int floorId, Map<String, int> data, String sessionId) async {
    try {
      final url = Uri.parse(uri);

      //return UserLocation(x: 133.15, y: 347.86);

      // Final payload structure
      final payload = {
        'buildingId': buildingId,
        'floorId': floorId,
        'featureVector': data,
        'sessionId': sessionId,
      };

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      print('Server response: ${response.statusCode} ${response.body}');
      if(response.statusCode == 200 || response.statusCode == 201) {
        final responseData = json.decode(response.body) as Map<String, dynamic>;
        // Check if response contains coordinates
        if (responseData.containsKey('svgX') &&
            responseData.containsKey('svgY')) {
          return UserLocation.fromJson(responseData);
        } else {
          print('Server response does not contain location coordinates');
          return null;
        }
      }else {
        print('HTTP Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Network error in sendAll: $e');
      return null;
    }
  }
  Future<UserLocation?> getEstimatedLocation(String uri, int buildingId, int floorId, Map<String, int> featureVector, UserLocation userLocation,String sessionId) async {
    try {
      final url = Uri.parse(uri);

      // Final payload structure
      final payload = {
        'buildingId': buildingId,
        'floorId': floorId,
        'featureVector': featureVector,
        'userLocation': userLocation.toString(),
        'sessionId': sessionId,
      };

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      print('Server response: ${response.statusCode} ${response.body}');
      if(response.statusCode == 200 || response.statusCode == 201) {
        final responseData = json.decode(response.body) as Map<String, dynamic>;
        // Check if response contains coordinates
        if (responseData.containsKey('svgX') &&
            responseData.containsKey('svgY')) {
          return UserLocation.fromJson(responseData);
        } else {
          print('Server response does not contain location coordinates');
          return null;
        }
      }else {
        print('HTTP Error: ${response.statusCode} - ${response.body}');
        return null;
      }
    } catch (e) {
      print('Network error in sendAll: $e');
      return null;
    }
  }

  Future<FloorData?> fetchOneCmSvg(int buildingId, int floorId) async {
    final uri = Uri.parse(Constants.getMetersToPixelScaleUri).replace(
      queryParameters: {
        'buildingId': buildingId.toString(),
        'floorId': floorId.toString(),
      },
    );

    try {
      final resp = await http.get(uri, headers: {'Accept': 'application/json'});

      if (resp.statusCode >= 200 && resp.statusCode < 300) {
        final raw = jsonDecode(resp.body);
        if (raw is Map<String, dynamic>) {
          return FloorData.fromJson(raw);
        }
        debugPrint('Unexpected JSON shape for floor data: $raw');
        return null;
      } else {
        debugPrint('fetchOneCmSvg failed: ${resp.statusCode} ${resp.body}');
        return null;
      }
    } catch (e) {
      debugPrint('fetchOneCmSvg error: $e');
      return null;
    }
  }

}