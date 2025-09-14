// import 'package:flutter/material.dart';
// import 'package:flutter_svg/flutter_svg.dart';
// import 'package:indigo_test/services/admin/admin_service.dart';
// import 'package:indigo_test/widgets/floor_picker.dart';
// import 'package:xml/xml.dart';
// import '../../constants.dart';
// import '../../models/Building.dart';
// import '../../models/Room.dart';
// import '../../services/general.dart';
//
// class AdminFloorView extends StatefulWidget {
//   final Building building;
//   final int selectedFloor;
//
//   const AdminFloorView({
//     super.key,
//     required this.building,
//     this.selectedFloor = 1, // Default floor
//   });
//
//   @override
//   State<AdminFloorView> createState() => _AdminFloorViewState();
// }
//
// class _AdminFloorViewState extends State<AdminFloorView> {
//   late int selectedFloor = 1;
//   String? svgData;
//   List<Room>? doors;
//   List<int> floorsList = [];
//   bool canContinue = false;
//   Room? selectedRoom;
//   bool isLoading = true;
//
//   // Add SVG dimensions variables
//   double svgWidth = 800;
//   double svgHeight = 800;
//
//   final TransformationController _transformationController = TransformationController();
//   final TextEditingController _roomNameController = TextEditingController();
//   final GeneralService generalService = GeneralService();
//
//   @override
//   void initState() {
//     super.initState();
//     selectedFloor = widget.selectedFloor;
//     _loadData(); // Load both SVG and doors
//   }
//
//   @override
//   void dispose() {
//     _roomNameController.dispose();
//     super.dispose();
//   }
//
//   // Combined loading method
//   Future<void> _loadData() async {
//     setState(() {
//       isLoading = true;
//     });
//
//     try {
//       // Load floors list first to determine the default floor
//       await loadFloorsList();
//
//       // Then load SVG and doors with the correct selected floor
//       await Future.wait([
//         loadSvg(),
//         loadDoors(),
//       ]);
//     } catch (e) {
//       print('Error loading data: $e');
//     } finally {
//       setState(() {
//         isLoading = false;
//       });
//     }
//   }
//
//   Future<void> loadFloorsList() async {
//     try {
//       floorsList = await generalService.getFloors(buildingId: widget.building.buildingId);
//
//       // Set the default floor to the first one in the list if not already set via widget parameter
//       if (floorsList.isNotEmpty && selectedFloor == widget.selectedFloor && widget.selectedFloor == 1) {
//         selectedFloor = floorsList.first; // Get first floor in the list
//       }
//     } catch (e) {
//       print('Error loading Floor List: $e');
//     }
//   }
//
//   // Method to parse SVG dimensions from the SVG string
//   void _parseSvgDimensions(String svgString) {
//     try {
//       final document = XmlDocument.parse(svgString);
//       final svgElement = document.findAllElements('svg').first;
//
//       // Try to get width and height attributes
//       final widthAttr = svgElement.getAttribute('width');
//       final heightAttr = svgElement.getAttribute('height');
//
//       if (widthAttr != null && heightAttr != null) {
//         // Remove 'px' or other units if present
//         final widthStr = widthAttr.replaceAll(RegExp(r'[^0-9.]'), '');
//         final heightStr = heightAttr.replaceAll(RegExp(r'[^0-9.]'), '');
//
//         svgWidth = double.tryParse(widthStr) ?? 800;
//         svgHeight = double.tryParse(heightStr) ?? 800;
//       } else {
//         // Try to get viewBox if width/height not available
//         final viewBox = svgElement.getAttribute('viewBox');
//         if (viewBox != null) {
//           final parts = viewBox.split(' ');
//           if (parts.length == 4) {
//             svgWidth = double.tryParse(parts[2]) ?? 800;
//             svgHeight = double.tryParse(parts[3]) ?? 800;
//           }
//         }
//       }
//
//       print('Parsed SVG dimensions: ${svgWidth}x${svgHeight}');
//     } catch (e) {
//       print('Error parsing SVG dimensions: $e');
//       // Fallback to default dimensions
//       svgWidth = 800;
//       svgHeight = 800;
//     }
//   }
//
//   Future<void> loadSvg() async {
//     try {
//       final url = Uri.parse(Constants.getFloorSvg);
//       svgData = await generalService.sendSvgRequest(url: url,
//           method: "GET",
//           queryParams: {
//             'buildingId': widget.building.buildingId.toString(),
//             'floorId': selectedFloor.toString(),
//           });
//
//       // Parse SVG dimensions
//       if (svgData != null) {
//         _parseSvgDimensions(svgData!);
//       }
//
//       // Reset the transformation to show the full SVG initially
//       WidgetsBinding.instance.addPostFrameCallback((_) {
//         _transformationController.value = Matrix4.identity();
//       });
//     } catch (e) {
//       print('Error loading SVG: $e');
//     }
//   }
//
//   Future<void> loadDoors() async {
//     try {
//       final url = Uri.parse(Constants.getDoorsName);
//       final fetchedDoors = await generalService.fetchRoomsFromFloor(url: url,
//           queryParams: {
//             'buildingId': widget.building.buildingId.toString(),
//             'floorId': selectedFloor.toString(),
//           });
//
//       setState(() {
//         doors = fetchedDoors;
//         _updateProgress();
//       });
//
//       // Reset the transformation to show the full SVG initially
//       WidgetsBinding.instance.addPostFrameCallback((_) {
//         _transformationController.value = Matrix4.identity();
//       });
//     } catch (e) {
//       print('Error loading doors: $e');
//     }
//   }
//
//   void _onDoorTap(Room room) {
//     print('Room ${room.id} selected');
//     setState(() {
//       selectedRoom = room;
//       _roomNameController.text = room.name ?? '';
//     });
//     _showRoomNamingDialog(room);
//   }
//
//   void _showRoomNamingDialog(Room room) {
//     showDialog(
//       context: context,
//       builder: (BuildContext context) {
//         return AlertDialog(
//           title: Text('Name Room ${room.id}'),
//           content: TextField(
//             controller: _roomNameController,
//             decoration: const InputDecoration(
//               hintText: 'Enter room name',
//               border: OutlineInputBorder(),
//             ),
//             autofocus: true,
//           ),
//           actions: [
//             TextButton(
//               onPressed: () => Navigator.of(context).pop(),
//               child: const Text('Cancel'),
//             ),
//             ElevatedButton(
//               onPressed: () {
//                 _saveRoomName(room);
//                 Navigator.of(context).pop();
//               },
//               child: const Text('Save'),
//             ),
//           ],
//         );
//       },
//     );
//   }
//
//   void _saveRoomName(Room room) {
//     setState(() {
//       room.name = _roomNameController.text.trim();
//       _updateProgress();
//     });
//     _roomNameController.clear();
//   }
//
//   void _updateProgress() {
//     if (doors == null) return;
//     final namedRooms = doors!.where((room) => room.name != null && room.name!.isNotEmpty).length;
//     final totalRooms = doors!.length;
//     canContinue = namedRooms == totalRooms;
//   }
//
//   Widget _buildFloorPicker() {
//     // Add null check for doors
//     if (doors == null) {
//       return Container(
//         padding: const EdgeInsets.all(16.0),
//         child: Row(
//           children: [
//             FloorPickerButton(
//               floorsList: floorsList,
//               selectedFloor: selectedFloor,
//               onFloorSelected: (value) {
//                 setState(() => selectedFloor = value);
//                 _loadData(); // Reload data for new floor
//               },
//             ),
//             const Spacer(),
//             const Text('Loading...'),
//           ],
//         ),
//       );
//     }
//
//     return Container(
//       padding: const EdgeInsets.all(16.0),
//       child: Row(
//         children: [
//           FloorPickerButton(
//             floorsList: floorsList,
//             selectedFloor: selectedFloor,
//             onFloorSelected: (value) {
//               setState(() => selectedFloor = value);
//               _loadData(); // Reload data for new floor
//             },
//           ),
//           const Spacer(),
//           Text('Progress: ${doors!.where((r) => r.name != null && r.name!.isNotEmpty).length}/${doors!.length}'),
//         ],
//       ),
//     );
//   }
//
//   Widget _buildDoorMarker(Room room) {
//     final isNamed = room.name != null && room.name!.isNotEmpty;
//
//     // Use the room coordinates directly since they should match the SVG coordinate system
//     return Positioned(
//       left: room.x.toDouble() - 15,
//       top: room.y.toDouble() - 15,
//       child: GestureDetector(
//         onTap: () {
//           print('Door ${room.id} tapped at (${room.x}, ${room.y})');
//           _onDoorTap(room);
//         },
//         child: Container(
//           width: 30,
//           height: 30,
//           decoration: BoxDecoration(
//             color: isNamed ? Colors.green.withValues(alpha: 0.8) : Colors.red.withValues(alpha: 0.8),
//             shape: BoxShape.circle,
//             border: Border.all(color: Colors.white, width: 2),
//             boxShadow: [
//               BoxShadow(
//                 color: Colors.black.withOpacity(0.5),
//                 blurRadius: 6,
//                 offset: const Offset(0, 3),
//               ),
//             ],
//           ),
//           child: Center(
//             child: Text(
//               room.id.toString(),
//               style: const TextStyle(
//                 color: Colors.white,
//                 fontSize: 12,
//                 fontWeight: FontWeight.bold,
//               ),
//             ),
//           ),
//         ),
//       ),
//     );
//   }
//
//   Widget _buildSvgWithOverlay() {
//     // Add null checks for both svgData and doors
//     if (svgData == null || doors == null) {
//       return const Center(
//         child: CircularProgressIndicator(),
//       );
//     }
//
//     return LayoutBuilder(
//       builder: (context, constraints) {
//         return InteractiveViewer(
//           transformationController: _transformationController,
//           boundaryMargin: const EdgeInsets.all(20),
//           minScale: 0.3,
//           maxScale: 5.0,
//           constrained: false,
//           child: Container(
//             width: svgWidth, // Use actual SVG width
//             height: svgHeight, // Use actual SVG height
//             child: Stack(
//               clipBehavior: Clip.none,
//               children: [
//                 // SVG Background - Use actual dimensions
//                 SvgPicture.string(
//                   svgData!,
//                   width: svgWidth,
//                   height: svgHeight,
//                   fit: BoxFit.fill,
//                 ),
//                 // Door Overlays
//                 ...doors!.map((room) => _buildDoorMarker(room)).toList(),
//               ],
//             ),
//           ),
//         );
//       },
//     );
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: Text(widget.building.name),
//         centerTitle: true,
//         actions: [
//           if (canContinue)
//             IconButton(
//               onPressed: () {
//                 ScaffoldMessenger.of(context).showSnackBar(
//                   const SnackBar(content: Text('All rooms have been named!')),
//                 );
//               },
//               icon: const Icon(Icons.check_circle, color: Colors.green),
//             ),
//         ],
//       ),
//       body: isLoading
//           ? const Center(
//         child: Column(
//           mainAxisAlignment: MainAxisAlignment.center,
//           children: [
//             CircularProgressIndicator(),
//             SizedBox(height: 16),
//             Text('Loading floor data...'),
//           ],
//         ),
//       )
//           : Column(
//         children: [
//           _buildFloorPicker(),
//           Expanded(
//             child: _buildSvgWithOverlay(),
//           ),
//         ],
//       ),
//       floatingActionButton: canContinue
//           ? FloatingActionButton.extended(
//         onPressed: () async {
//           try {
//             await AdminService.updateRoomNames(
//               buildingId: widget.building.buildingId,
//               floorId: selectedFloor,
//               rooms: doors!,
//             );
//             Navigator.of(context).pop();
//             ScaffoldMessenger.of(context).showSnackBar(
//               const SnackBar(content: Text('Room names updated successfully!')),
//             );
//           } catch (e) {
//             Navigator.of(context).pop();
//             ScaffoldMessenger.of(context).showSnackBar(
//               SnackBar(content: Text('Failed to update room names: $e')),
//             );
//           }
//         },
//         icon: const Icon(Icons.arrow_forward),
//         label: const Text('Continue'),
//         backgroundColor: Colors.green,
//       )
//           : null,
//     );
//   }
// }

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:indigo_test/services/admin/admin_service.dart';
import 'package:indigo_test/widgets/floor_picker.dart';
import 'package:xml/xml.dart';
import '../../constants.dart';
import '../../models/Building.dart';
import '../../models/Room.dart';
import '../../services/general.dart';
import '../../widgets/no_floors_in_building.dart'; // Import your empty state widget

class AdminFloorView extends StatefulWidget {
  final Building building;
  final int selectedFloor;

  const AdminFloorView({
    super.key,
    required this.building,
    this.selectedFloor = 1, // Default floor
  });

  @override
  State<AdminFloorView> createState() => _AdminFloorViewState();
}

class _AdminFloorViewState extends State<AdminFloorView> {
  late int selectedFloor = 1;
  String? svgData;
  List<Room>? doors;
  List<int> floorsList = [];
  bool canContinue = false;
  Room? selectedRoom;
  bool isLoading = true;
  bool isFloorsLoading = true; // Added to track floors loading specifically

  // Add SVG dimensions variables
  double svgWidth = 800;
  double svgHeight = 800;

  final TransformationController _transformationController = TransformationController();
  final TextEditingController _roomNameController = TextEditingController();
  final GeneralService generalService = GeneralService();

  @override
  void initState() {
    super.initState();
    selectedFloor = widget.selectedFloor;
    _loadData(); // Load both SVG and doors
  }

  @override
  void dispose() {
    _roomNameController.dispose();
    super.dispose();
  }

  // Combined loading method
  Future<void> _loadData() async {
    setState(() {
      isLoading = true;
      isFloorsLoading = true;
    });

    try {
      // Load floors list first to determine the default floor
      await loadFloorsList();

      // If no floors found, stop loading here
      if (floorsList.isEmpty) {
        setState(() {
          isFloorsLoading = false;
          isLoading = false;
        });
        return;
      }

      // Mark floors loading as complete
      setState(() {
        isFloorsLoading = false;
      });

      // Then load SVG and doors with the correct selected floor
      await Future.wait([
        loadSvg(),
        loadDoors(),
      ]);
    } catch (e) {
      print('Error loading data: $e');
    } finally {
      setState(() {
        isLoading = false;
        isFloorsLoading = false;
      });
    }
  }

  Future<void> loadFloorsList() async {
    try {
      floorsList = await generalService.getFloors(buildingId: widget.building.buildingId);

      // Set the default floor to the first one in the list if not already set via widget parameter
      if (floorsList.isNotEmpty && selectedFloor == widget.selectedFloor && widget.selectedFloor == 1) {
        selectedFloor = floorsList.first; // Get first floor in the list
      }
    } catch (e) {
      print('Error loading Floor List: $e');
    }
  }

  // Method to parse SVG dimensions from the SVG string
  void _parseSvgDimensions(String svgString) {
    try {
      final document = XmlDocument.parse(svgString);
      final svgElement = document.findAllElements('svg').first;

      // Try to get width and height attributes
      final widthAttr = svgElement.getAttribute('width');
      final heightAttr = svgElement.getAttribute('height');

      if (widthAttr != null && heightAttr != null) {
        // Remove 'px' or other units if present
        final widthStr = widthAttr.replaceAll(RegExp(r'[^0-9.]'), '');
        final heightStr = heightAttr.replaceAll(RegExp(r'[^0-9.]'), '');

        svgWidth = double.tryParse(widthStr) ?? 800;
        svgHeight = double.tryParse(heightStr) ?? 800;
      } else {
        // Try to get viewBox if width/height not available
        final viewBox = svgElement.getAttribute('viewBox');
        if (viewBox != null) {
          final parts = viewBox.split(' ');
          if (parts.length == 4) {
            svgWidth = double.tryParse(parts[2]) ?? 800;
            svgHeight = double.tryParse(parts[3]) ?? 800;
          }
        }
      }

      print('Parsed SVG dimensions: ${svgWidth}x${svgHeight}');
    } catch (e) {
      print('Error parsing SVG dimensions: $e');
      // Fallback to default dimensions
      svgWidth = 800;
      svgHeight = 800;
    }
  }

  Future<void> loadSvg() async {
    try {
      final url = Uri.parse(Constants.getFloorSvg);
      svgData = await generalService.sendSvgRequest(url: url,
          method: "GET",
          queryParams: {
            'buildingId': widget.building.buildingId.toString(),
            'floorId': selectedFloor.toString(),
          });

      // Parse SVG dimensions
      if (svgData != null) {
        _parseSvgDimensions(svgData!);
      }

      // Reset the transformation to show the full SVG initially
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _transformationController.value = Matrix4.identity();
      });
    } catch (e) {
      print('Error loading SVG: $e');
    }
  }

  Future<void> loadDoors() async {
    try {
      final url = Uri.parse(Constants.getDoorsName);
      final fetchedDoors = await generalService.fetchRoomsFromFloor(url: url,
          queryParams: {
            'buildingId': widget.building.buildingId.toString(),
            'floorId': selectedFloor.toString(),
          });

      setState(() {
        doors = fetchedDoors;
        _updateProgress();
      });

      // Reset the transformation to show the full SVG initially
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _transformationController.value = Matrix4.identity();
      });
    } catch (e) {
      print('Error loading doors: $e');
    }
  }

  void _onDoorTap(Room room) {
    print('Room ${room.id} selected');
    setState(() {
      selectedRoom = room;
      _roomNameController.text = room.name ?? '';
    });
    _showRoomNamingDialog(room);
  }

  void _showRoomNamingDialog(Room room) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Name Room ${room.id}'),
          content: TextField(
            controller: _roomNameController,
            decoration: const InputDecoration(
              hintText: 'Enter room name',
              border: OutlineInputBorder(),
            ),
            autofocus: true,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                _saveRoomName(room);
                Navigator.of(context).pop();
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  void _saveRoomName(Room room) {
    setState(() {
      room.name = _roomNameController.text.trim();
      _updateProgress();
    });
    _roomNameController.clear();
  }

  void _updateProgress() {
    if (doors == null) return;
    final namedRooms = doors!.where((room) => room.name != null && room.name!.isNotEmpty).length;
    final totalRooms = doors!.length;
    canContinue = namedRooms == totalRooms;
  }

  Widget _buildFloorPicker() {
    // Add null check for doors
    if (doors == null) {
      return Container(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            FloorPickerButton(
              floorsList: floorsList,
              selectedFloor: selectedFloor,
              onFloorSelected: (value) {
                setState(() => selectedFloor = value);
                _loadData(); // Reload data for new floor
              },
            ),
            const Spacer(),
            const Text('Loading...'),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        children: [
          FloorPickerButton(
            floorsList: floorsList,
            selectedFloor: selectedFloor,
            onFloorSelected: (value) {
              setState(() => selectedFloor = value);
              _loadData(); // Reload data for new floor
            },
          ),
          const Spacer(),
          Text('Progress: ${doors!.where((r) => r.name != null && r.name!.isNotEmpty).length}/${doors!.length}'),
        ],
      ),
    );
  }

  Widget _buildDoorMarker(Room room) {
    final isNamed = room.name != null && room.name!.isNotEmpty;

    // Use the room coordinates directly since they should match the SVG coordinate system
    return Positioned(
      left: room.x.toDouble() - 15,
      top: room.y.toDouble() - 15,
      child: GestureDetector(
        onTap: () {
          print('Door ${room.id} tapped at (${room.x}, ${room.y})');
          _onDoorTap(room);
        },
        child: Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: isNamed ? Colors.green.withValues(alpha: 0.8) : Colors.red.withValues(alpha: 0.8),
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.5),
                blurRadius: 6,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Center(
            child: Text(
              room.id.toString(),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSvgWithOverlay() {
    // Add null checks for both svgData and doors
    if (svgData == null || doors == null) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        return InteractiveViewer(
          transformationController: _transformationController,
          boundaryMargin: const EdgeInsets.all(20),
          minScale: 0.3,
          maxScale: 5.0,
          constrained: false,
          child: Container(
            width: svgWidth, // Use actual SVG width
            height: svgHeight, // Use actual SVG height
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                // SVG Background - Use actual dimensions
                SvgPicture.string(
                  svgData!,
                  width: svgWidth,
                  height: svgHeight,
                  fit: BoxFit.fill,
                ),
                // Door Overlays
                ...doors!.map((room) => _buildDoorMarker(room)).toList(),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.building.name),
        centerTitle: true,
        actions: [
          if (canContinue)
            IconButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('All rooms have been named!')),
                );
              },
              icon: const Icon(Icons.check_circle, color: Colors.green),
            ),
        ],
      ),
      body: isFloorsLoading
          ? const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),

            Text('Loading floors...'),
          ],
        ),
      )
          : floorsList.isEmpty
          ? buildEmptyState()
          : isLoading
          ? const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading floor data...'),
          ],
        ),
      )
          : Column(
        children: [
          _buildFloorPicker(),
          Expanded(
            child: _buildSvgWithOverlay(),
          ),
        ],
      ),
      floatingActionButton: canContinue
          ? FloatingActionButton.extended(
        onPressed: () async {
          try {
            await AdminService.updateRoomNames(
              buildingId: widget.building.buildingId,
              floorId: selectedFloor,
              rooms: doors!,
            );
            Navigator.of(context).pop();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Room names updated successfully!')),
            );
          } catch (e) {
            Navigator.of(context).pop();
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Failed to update room names: $e')),
            );
          }
        },
        icon: const Icon(Icons.arrow_forward),
        label: const Text('Continue'),
        backgroundColor: Colors.green,
      )
          : null,
    );
  }
}