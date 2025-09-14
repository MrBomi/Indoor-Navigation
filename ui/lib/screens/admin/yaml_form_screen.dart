import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// Class to hold both values
class YamlFormResult {
  final String yaml;
  final int floorNumber;

  YamlFormResult({required this.yaml, required this.floorNumber});
}


class YamlDetailsForm extends StatefulWidget {
  final String dwgFile;

  const YamlDetailsForm({super.key, required this.dwgFile});

  @override
  State<YamlDetailsForm> createState() => _YamlDetailsFormState();
}

class _YamlDetailsFormState extends State<YamlDetailsForm> {
  final _formKey = GlobalKey<FormState>();

  final _floorNumberController = TextEditingController();
  final _wallLayerController = TextEditingController();
  final _doorLayerController = TextEditingController();
  final _roofLayerController = TextEditingController();
  final _scaleController = TextEditingController();

  bool _isFormFilled = false;

  @override
  void initState() {
    super.initState();
    // Listen to all fields to update button state
    _wallLayerController.addListener(_checkFormFilled);
    _doorLayerController.addListener(_checkFormFilled);
    _roofLayerController.addListener(_checkFormFilled);
    _scaleController.addListener(_checkFormFilled);
    _floorNumberController.addListener(_checkFormFilled);
  }

  @override
  void dispose() {
    _wallLayerController.dispose();
    _doorLayerController.dispose();
    _roofLayerController.dispose();
    _scaleController.dispose();
    _floorNumberController.dispose();
    super.dispose();
  }

  String generateYaml({required String wall, required String door, required String roof, required String precision, required String fileName, required String floorNumber})
  {
    final fileNameWithoutExtension = fileName.split('.').first;

    return '''
    app:
      name: Graph Maker
      version: 1.0
    
    file:
      input_name: $fileNameWithoutExtension.dxf
      output_name: static/output/$fileNameWithoutExtension.graphml
      svg_output_name: static/output/$fileNameWithoutExtension.svg
      json_output_name: static/output/${fileNameWithoutExtension}_points.json
      precision: $precision
      floor_number: $floorNumber
    
    graph:
      node_size: 30.0
      scale: $precision
      offset_cm: 200
    
    layers:
      wall_layer:
        name: $wall
        color: "#000000"
        opacity: 0.5
    
      door_layer:
        name: $door
        color: "#FF0000"
        opacity: 0.5
    
      roof_layer:
        name: $roof
        color: "#00FF00"
        opacity: 0.5
    ''';
  }

  void _checkFormFilled() {
    final filled = _wallLayerController.text.isNotEmpty &&
        _doorLayerController.text.isNotEmpty &&
        _roofLayerController.text.isNotEmpty &&
        _scaleController.text.isNotEmpty &&
        _floorNumberController.text.isNotEmpty;

    if (filled != _isFormFilled) {
      setState(() {
        _isFormFilled = filled;
      });
    }
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {

      final yaml = generateYaml(
        wall: _wallLayerController.text,
        door: _doorLayerController.text,
        roof: _roofLayerController.text,
        precision: _scaleController.text,
        fileName: widget.dwgFile,
        floorNumber: _floorNumberController.text,
      );

      final floorNumber = int.tryParse(_floorNumberController.text) ?? 1;
      // Send yaml + file to server here
      Navigator.pop(context, YamlFormResult(
          yaml: yaml,
          floorNumber: floorNumber
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Enter DWG Details')),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                Text('File: ${widget.dwgFile}'),
                const SizedBox(height: 16),

                TextFormField(
                  controller: _floorNumberController,
                  decoration: const InputDecoration(labelText: 'Floor Number'),
                  keyboardType: TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                  ],
                  validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                ),
                TextFormField(
                  controller: _wallLayerController,
                  decoration: const InputDecoration(labelText: 'Wall Layer Name'),
                  validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                ),
                TextFormField(
                  controller: _doorLayerController,
                  decoration: const InputDecoration(labelText: 'Door Layer Name'),
                  validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                ),
                TextFormField(
                  controller: _roofLayerController,
                  decoration: const InputDecoration(labelText: 'Roof Layer Name'),
                  validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                ),
                TextFormField(
                  controller: _scaleController,
                  decoration: const InputDecoration(labelText: 'Scale'),
                  keyboardType: TextInputType.numberWithOptions(decimal: true),
                  validator: (v) => v == null || v.isEmpty ? 'Required' : null,
                ),

                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _isFormFilled? _submit : null,
                  child: const Text('Upload'),
                ),
              ],
            ),
          ),
        ),
      )
    );
  }
}
