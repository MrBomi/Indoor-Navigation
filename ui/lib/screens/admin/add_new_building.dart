import 'package:flutter/material.dart';
import 'package:google_places_flutter/google_places_flutter.dart';
import 'package:google_places_flutter/model/place_type.dart';
import 'package:google_places_flutter/model/prediction.dart';
import '../../services/admin/new_building_service.dart';

class AddNewBuildingScreen extends StatefulWidget {
  const AddNewBuildingScreen({super.key});

  @override
  State<AddNewBuildingScreen> createState() => _AddNewBuildingScreenState();
}

class _AddNewBuildingScreenState extends State<AddNewBuildingScreen> {
  late final FocusNode _buildingNameFocusNode;
  late final FocusNode _cityFocusNode;
  late final FocusNode _streetFocusNode;

  final _formKey = GlobalKey<FormState>();
  final _buildingNameController = TextEditingController();
  final _cityController = TextEditingController();
  final _streetController = TextEditingController();
  final BuildingService _buildingService = BuildingService();

  //TODO change this to your actual Google API key
  //static String get _googleApiKey => dotenv.env['GOOGLE_API_KEY'] ?? '';
  static const String _googleApiKey = "AIzaSyA8i8hLWWILASQhDsH5qANb-w_hOQ5PKjs";

  bool _isLoading = false;


  @override
  void initState() {
    super.initState();
    _buildingNameFocusNode = FocusNode();
    _cityFocusNode         = FocusNode();
    _streetFocusNode       = FocusNode();
  }

  @override
  void dispose() {
    _buildingNameController.dispose();
    _cityController.dispose();
    _streetController.dispose();

    _buildingNameFocusNode.dispose();
    _cityFocusNode.dispose();
    _streetFocusNode.dispose();
    super.dispose();
  }

  Future<void> _createBuilding() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final status = await _buildingService.createBuilding(
        name: _buildingNameController.text.trim(),
        city: _cityController.text.trim(),
        address: _streetController.text.trim(),
      );

      if (mounted) {
        Navigator.pop(context, status);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Building created successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to create building: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: const Color(0xFF4F46E5),
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text('Add New Building'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),

                // 1️⃣ Building Name
                TextFormField(
                  focusNode: _buildingNameFocusNode,
                  controller: _buildingNameController,
                  validator: (v) => v!.isEmpty ? 'Required' : null,
                  decoration: InputDecoration(
                    labelText: 'Building Name *',
                    hintText: 'Enter building name',
                    prefixIcon: const Icon(Icons.business),
                    filled: true,
                    fillColor: Colors.blue.shade50,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Colors.blue.shade100),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide:
                      const BorderSide(color: Color(0xFF4F46E5), width: 2),
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // 2️⃣ City (Places autocomplete)
                GooglePlaceAutoCompleteTextField(
                  focusNode: _cityFocusNode,
                  textEditingController: _cityController,
                  googleAPIKey: _googleApiKey,
                  debounceTime: 800,
                  countries: ['il'],
                  placeType: PlaceType.cities,
                  isLatLngRequired: false,
                  inputDecoration: InputDecoration(
                    labelText: 'City *',
                    hintText: 'Search for city in Israel',
                    prefixIcon: const Icon(Icons.location_city),
                    filled: true,
                    fillColor: Colors.blue.shade50,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Colors.blue.shade100),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide:
                      const BorderSide(color: Color(0xFF4F46E5), width: 2),
                    ),
                  ),
                  itemClick: (Prediction p) {
                    final city = p.structuredFormatting?.mainText ?? '';
                    _cityController.text = city;
                    FocusScope.of(context).requestFocus(_streetFocusNode);
                  },
                  isCrossBtnShown: false,
                  seperatedBuilder: Divider(color: Colors.grey.shade300, height: 1),
                  itemBuilder: (context, index, Prediction p) => ListTile(
                    leading: const Icon(Icons.location_city, size: 20),
                    title: Text(
                      p.structuredFormatting?.mainText
                          ?? p.description ?? '',
                      style: const TextStyle(fontSize: 14),
                    ),
                    subtitle: p.structuredFormatting?.secondaryText != null
                        ? Text(
                      p.structuredFormatting!.secondaryText!,
                      style: const TextStyle(fontSize: 12),
                    )
                        : null,
                  ),
                ),

                const SizedBox(height: 20),

                // 3️⃣ Street (Places autocomplete)
                GooglePlaceAutoCompleteTextField(
                  focusNode: _streetFocusNode,
                  textEditingController: _streetController,
                  googleAPIKey: _googleApiKey,
                  debounceTime: 800,
                  isLatLngRequired: false,
                  countries: ['il'],
                  placeType: PlaceType.address, // only addresses
                  inputDecoration: InputDecoration(
                    labelText: 'Street Address *',
                    hintText: 'Enter street address',
                    prefixIcon: const Icon(Icons.place),
                    filled: true,
                    fillColor: Colors.blue.shade50,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Colors.blue.shade100),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide:
                      const BorderSide(color: Color(0xFF4F46E5), width: 2),
                    ),
                  ),
                  itemClick: (Prediction p) {
                    final street = p.structuredFormatting?.mainText ?? '';
                    _streetController.text = street;
                    FocusScope.of(context).unfocus();
                  },
                  isCrossBtnShown: false,
                  seperatedBuilder: Divider(color: Colors.grey.shade300, height: 1),
                  itemBuilder: (context, index, Prediction p) => ListTile(
                    leading: const Icon(Icons.place, size: 20),
                    title: Text(
                      p.structuredFormatting?.mainText ?? '',
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                ),


                const SizedBox(height: 40),

                ElevatedButton(
                  onPressed: _isLoading ? null : _createBuilding,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4F46E5),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Done', style: TextStyle(fontSize: 16)),
                ),

                const SizedBox(height: 16),
                const Text(
                  '* Required fields',
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
