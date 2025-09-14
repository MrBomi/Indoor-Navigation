import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import '../../constants.dart';


class BuildingService {

  // Replace with your actual API base URL
  static const String _baseUrl = 'https://your-api-endpoint.com/api';

  // HTTP client instance
  final http.Client _client = http.Client();

  // Headers for API requests
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  Future<PlatformFile?> pickDwgFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        withData: true, // This is CRUCIAL - loads file bytes into memory
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        PlatformFile file = result.files.first;

        // Double check that bytes were loaded
        if (file.bytes != null && file.bytes!.isNotEmpty) {
          print('File selected: ${file.name}');
          print('File size: ${file.bytes!.length} bytes');
          return file;
        } else {
          print('File bytes are null or empty');
          return null;
        }
      }

      print('No file selected');
      return null;
    } catch (e) {
      print('Error picking file: $e');
      return null;
    }
  }


  /// Creates a new building
  ///
  /// Sends a POST request to create a building with the provided name and address
  /// Returns the created Building object with the assigned buildingId
  Future<int> createBuilding({
    required String name,
    required String city,
    required String address,
  }) async {
    try {
      final url = Uri.parse(Constants.newBuilding).replace(
        queryParameters: {
          'name': name,
          'city': city,
          'address': address,
        },
      );

      final response = await _client.post(
        url,
        headers: _headers,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return response.statusCode;
      } else {
        throw BuildingServiceException(
          'Failed to create building: ${response.statusCode} - ${response.reasonPhrase}',
        );
      }
    } on http.ClientException catch (e) {
      throw BuildingServiceException('Network error: ${e.message}');
    } on FormatException catch (e) {
      throw BuildingServiceException('Invalid response format: ${e.message}');
    } catch (e) {
      throw BuildingServiceException('Unexpected error: ${e.toString()}');
    }
  }

  // /// Updates an existing building
  // ///
  // /// Sends a PUT request to update building information
  // Future<Building> updateBuilding({
  //   required int buildingId,
  //   required String name,
  //   required String address,
  // }) async {
  //   try {
  //     final url = Uri.parse('$_baseUrl/buildings/$buildingId');
  //
  //     final requestBody = {
  //       'name': name,
  //       'address': address,
  //     };
  //
  //     final response = await _client.put(
  //       url,
  //       headers: _headers,
  //       body: json.encode(requestBody),
  //     );
  //
  //     if (response.statusCode == 200) {
  //       final responseData = json.decode(response.body);
  //
  //       return Building(
  //         buildingId: responseData['id'] ?? responseData['buildingId'],
  //         name: responseData['name'],
  //         city: responseData['city'],
  //         address: responseData['address'],
  //       );
  //     } else {
  //       throw BuildingServiceException(
  //         'Failed to update building: ${response.statusCode} - ${response.reasonPhrase}',
  //       );
  //     }
  //   } on http.ClientException catch (e) {
  //     throw BuildingServiceException('Network error: ${e.message}');
  //   } on FormatException catch (e) {
  //     throw BuildingServiceException('Invalid response format: ${e.message}');
  //   } catch (e) {
  //     throw BuildingServiceException('Unexpected error: ${e.toString()}');
  //   }
  // }
  //
  // /// Deletes a building
  // ///
  // /// Sends a DELETE request to remove a building
  // Future<void> deleteBuilding(int buildingId) async {
  //   try {
  //     final url = Uri.parse('$_baseUrl/buildings/$buildingId');
  //
  //     final response = await _client.delete(
  //       url,
  //       headers: _headers,
  //     );
  //
  //     if (response.statusCode != 200 && response.statusCode != 204) {
  //       throw BuildingServiceException(
  //         'Failed to delete building: ${response.statusCode} - ${response.reasonPhrase}',
  //       );
  //     }
  //   } on http.ClientException catch (e) {
  //     throw BuildingServiceException('Network error: ${e.message}');
  //   } catch (e) {
  //     throw BuildingServiceException('Unexpected error: ${e.toString()}');
  //   }
  // }

  /// Disposes the HTTP client
  void dispose() {
    _client.close();
  }
}

/// Custom exception class for BuildingService errors
class BuildingServiceException implements Exception {
  final String message;

  const BuildingServiceException(this.message);

  @override
  String toString() => 'BuildingServiceException: $message';
}