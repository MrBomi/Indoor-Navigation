import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';
import 'package:indigo_test/screens/admin/yaml_form_screen.dart';
import 'package:indigo_test/services/admin/admin_service.dart';
import '../../models/Building.dart';

import '../../services/admin/new_building_service.dart';
import '../data_collection/wifi_fingerprint_screen.dart';
import 'admin_floor_view.dart';
import 'calibration_screen.dart';

class AdminBuildingCard extends StatelessWidget {
  final Building building;
  final VoidCallback? onTap; // Nullable in case it's optional

  const AdminBuildingCard({
    super.key,
    required this.building,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => AdminFloorView(building: building ),
            ),
          );
        },
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.grey.shade200,
          ),
          child: Padding(
            padding: const EdgeInsets.all(6.0),
            child: SvgPicture.asset(
              'assets/icons/building.svg',
              fit: BoxFit.contain,
            ),
          ),
        ),
        title: Text(
          building.name,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(building.address),
        trailing: _MoreOptionsMenu(building: building,),
      ),
    );
  }
}

class _MoreOptionsMenu extends StatelessWidget {
  final Building building;

  const _MoreOptionsMenu({
    super.key,
    required this.building,
  });

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      tooltip: 'More options',
      onSelected: (value) => _handleSelection(context, value),
      itemBuilder: (BuildContext context) => [
        const PopupMenuItem(
          value: 'Add',
          child: _MenuItemWithIcon(icon: Icons.add, text: 'Add Floor'),
        ),
        const PopupMenuItem(
          value: 'Edit',
          child: _MenuItemWithIcon(icon: Icons.edit, text: 'Edit Floors'),
        ),
        const PopupMenuItem(
          value: 'Calibrate Location',
          child: _MenuItemWithIcon(icon: Icons.compass_calibration, text: 'Calibrate floor plan'),
        ),
        const PopupMenuItem(
          value: 'Delete Building',
          child: _MenuItemWithIcon(icon: Icons.delete, text: 'Delete Building'),
        ),
      ],
    );
  }

  Future<void> _handleSelection(BuildContext context, String value) async {
    switch (value) {
      case 'Edit':
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Edit pressed')),
        );
        break;
      case 'Delete Building':
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Delete pressed')),
        );
        break;
      case 'Add':
        try {
          final file = await BuildingService().pickDwgFile();

          if (file == null) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('No file selected or could not read file')),
            );
            return;
          }

          print('File picked successfully: ${file.name}, Size: ${file.bytes!.length}');

          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => YamlDetailsForm(dwgFile: file.name),
            ),
          );

          if (result != null && result is YamlFormResult) {
            final yaml = result.yaml;
            final floorNumber = result.floorNumber;

            print('Floor Number: $floorNumber');
            print('YAML: $yaml');

            // Show progress dialog
            showDialog(
              context: context,
              barrierDismissible: false, // Prevent dismissing by tapping outside
              builder: (BuildContext dialogContext) {
                return WillPopScope(
                  onWillPop: () async => false, // Prevent back button from closing dialog
                  child: AlertDialog(
                    content: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Processing DXF file...'),
                        SizedBox(height: 8),
                        Text(
                          'This may take a few moments',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ),
                );
              },
            );

            try {
              final svgString = await AdminService.uploadDxfAndYaml(
                fileName: file.name,
                buildingId: building.buildingId,
                floorId: floorNumber,
                fileBytes: file.bytes!,
                yaml: yaml,
              );

              // Close progress dialog
              Navigator.of(context).pop();

              // Navigate to calibration screen
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => CalibrationScreen(
                    svg: svgString,
                    building: building,
                    floor: floorNumber,
                  ),
                ),
              );
            } catch (e) {
              // Close progress dialog first
              Navigator.of(context).pop();

              print('Upload error: $e');
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Error uploading file: ${e.toString()}')),
              );
            }
          }
        } catch (e) {
          print('File picker error: $e');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error selecting file: ${e.toString()}')),
          );
        }
        break;
        case 'Calibrate Location':
        //Navigate to calibration screen
          Navigator.push(
            context,
            MaterialPageRoute(
              // builder: (context) => MagneticPositioningWithCompass(
              //   building: building,
              // ),
              builder: (context) => WifiCollectionFingerprint(
                building: building,
              ),
            ),
          );
        break;
    }
  }
}

class _MenuItemWithIcon extends StatelessWidget {
  final IconData icon;
  final String text;

  const _MenuItemWithIcon({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18),
        const SizedBox(width: 8),
        Text(text),
      ],
    );
  }
}
