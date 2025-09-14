import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:indigo_test/constants.dart';

import '../models/Room.dart';


class GeneralService {

  Future<dynamic> sendRequest({
    required Uri url,
    String method = "GET",
    Map<String, String>? queryParams,
    Map<String, String>? headers,
    dynamic body,
  }) async {
    Uri finalUrl = url;

    // attach query params if needed
    if (queryParams != null && queryParams.isNotEmpty) {
      finalUrl = url.replace(queryParameters: queryParams);
    }

    // default headers
    final defaultHeaders = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...?headers,
    };

    http.Response resp;

    try {
        resp = await http.get(finalUrl, headers: defaultHeaders);
    } catch (e) {
      throw Exception("Network error: $e");
    }

    // check status
    if (resp.statusCode < 200 || resp.statusCode >= 300) {
      throw Exception(
          "Request failed [${resp.statusCode}]: ${resp.body}");
    }

    // parse JSON
    try {
      return jsonDecode(resp.body);
    } catch (_) {
      return resp.body; // fallback in case it's plain text/SVG
    }
  }

  Future<String> sendSvgRequest({
    required Uri url,
    required String method,
    Map<String, String>? headers,
    Map<String, dynamic>? body,
    Map<String, String>? queryParams,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    try {
      final finalUrl = queryParams != null
          ? url.replace(queryParameters: queryParams)
          : url;

      http.Response response;

      switch (method.toUpperCase()) {
        case 'POST':
          response = await http
              .post(url, headers: headers, body: json.encode(body))
              .timeout(timeout);
          break;
        case 'GET':
          response = await http
              .get(finalUrl, headers: headers)
              .timeout(timeout);
          break;
        case 'PUT':
          response = await http
              .put(url, headers: headers, body: json.encode(body))
              .timeout(timeout);
          break;
        case 'DELETE':
          response = await http
              .delete(url, headers: headers)
              .timeout(timeout);
          break;
        default:
          throw Exception('Unsupported HTTP method: $method');
      }

      if (response.statusCode == 200 || response.statusCode == 201) {
        final contentType = response.headers['content-type'] ?? '';

        if (contentType.contains('image/svg+xml') || contentType.contains('text/xml')) {
          return response.body;
        }

        try {
          final jsonData = json.decode(response.body);
          if (jsonData is Map<String, dynamic>) {
            if (jsonData.containsKey('svg_data')) return jsonData['svg_data'] as String;
            if (jsonData.containsKey('data')) return jsonData['data'] as String;
          }
        } catch (_) {
          // Not JSON - return raw
        }

        throw Exception('SVG data not found in response');
      } else {
        throw Exception('Request failed: ${response.statusCode} - ${response.reasonPhrase}');
      }
    } catch (e) {
      print('Error in sendSvgRequest: $e');
      if (e.toString().contains('SocketException') || e.toString().contains('Connection')) {
        throw Exception('Network error: Please check your internet connection');
      }
      rethrow;
    }
  }

  Future<List<String>> fetchRoomsNameFromFloor({
  required Uri url,
  Map<String, String>? queryParams,
  Duration timeout = const Duration(seconds: 30)}) async {
    try {

      final finalUrl = queryParams != null
          ? url.replace(queryParameters: queryParams)
          : url;

      // Send HTTP GET request
      final response = await http
          .get(finalUrl)
          .timeout(timeout);


      // Check if request was successful
      if (response.statusCode == 200) {
        // Parse JSON response
        final List<dynamic> jsonData = json.decode(response.body);

        // Extract names from each object in the array
        final List<String> names = jsonData
            .map((item) => item['name'] as String)
            .toList();

        return names;
      } else {
        throw Exception('Failed to load data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching names: $e');
    }
  }

  Future<List<Room>> fetchRoomsFromFloor({
    required Uri url,
    Map<String, String>? queryParams,
    Duration timeout = const Duration(seconds: 30)}) async {
    try {
      final finalUrl = queryParams != null
          ? url.replace(queryParameters: queryParams)
          : url;

      // Send HTTP GET request
      final response = await http
          .get(finalUrl)
          .timeout(timeout);

      // Check if request was successful
      if (response.statusCode == 200) {
        // Parse JSON response
        final List<dynamic> jsonData = json.decode(response.body);

        // Convert each JSON object to Room instance
        final List<Room> rooms = jsonData
            .map((json) => Room.fromJson(json as Map<String, dynamic>))
            .toList();

        return rooms;
      } else {
        throw Exception('Failed to load rooms: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching rooms: $e');
    }
  }

  Future<List<int>> getFloors({required int buildingId}) async {
    final uri = Uri.parse(Constants.getAllFloorsInBuilding).replace(
      queryParameters: {'buildingId': buildingId.toString()},
    );

    final response = await http.get(uri);
    if (response.statusCode == 200) {
      // Example body: [1,2,3]
      final List<dynamic> jsonList = jsonDecode(response.body);
      return jsonList.map((e) => e as int).toList();
    } else if (response.statusCode == 400) {
      throw Exception('Missing buildingId');
    } else {
      throw Exception('Failed to load floors: ${response.statusCode}');
    }
  }
}