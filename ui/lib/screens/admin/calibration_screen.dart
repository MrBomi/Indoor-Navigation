import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter/services.dart';
import '../../models/Building.dart';
import '../../services/admin/calibration_service.dart';
import '../../widgets/dialogs/north_alignment_dialog.dart';
import 'admin_floor_view.dart';

class CalibrationScreen extends StatefulWidget {
  final String svg;
  final Building building;
  final int floor;

  const CalibrationScreen({
    super.key,
    required this.svg,
    required this.building,
    required this.floor,
  });

  @override
  State<CalibrationScreen> createState() => _CalibrationScreenState();
}

class _CalibrationScreenState extends State<CalibrationScreen> {
  String? svgData;
  final TransformationController _transformationController = TransformationController();
  final TextEditingController _distanceController = TextEditingController();
  final CalibrationService _calibrationService = CalibrationService();

  Offset? firstPoint;
  Offset? secondPoint;
  bool isLoading = false;
  bool canSubmit = false;
  bool isNavigateMode = true; // true = navigate/zoom, false = calibrate/tap
  double pdrNorthOffset = 0.0; // degrees to align SVG north with magnetic north

  @override
  void initState() {
    super.initState();
    svgData = widget.svg; // Use the SVG passed from the previous screen

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _showNorthAlignmentDialog();
      }
    });
    //loadSvg();
  }

  @override
  void dispose() {
    _distanceController.dispose();
    super.dispose();
  }


  void _onSvgTap(TapDownDetails details) {
    // Only allow tapping when in calibrate mode
    if (isNavigateMode) return;

    if (firstPoint == null) {
      setState(() {
        firstPoint = details.localPosition;
        print('First point set at: ${firstPoint!.dx}, ${firstPoint!.dy}');
      });
    } else if (secondPoint == null) {
      setState(() {
        secondPoint = details.localPosition;
        print('Second point set at: ${secondPoint!.dx}, ${secondPoint!.dy}');
        _updateSubmitStatus();
      });
      _showDistanceDialog();
    }
  }

  void _toggleMode() {
    setState(() {
      isNavigateMode = !isNavigateMode;
    });
  }

  void _resetPoints() {
    setState(() {
      firstPoint = null;
      secondPoint = null;
      canSubmit = false;
      _distanceController.clear();
    });
  }

  void _updateSubmitStatus() {
    setState(() {
      canSubmit = firstPoint != null &&
          secondPoint != null &&
          _distanceController.text.trim().isNotEmpty;
    });
  }

  void _showDistanceDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Enter Distance'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Enter the real distance between the two points in centimeters:'),
              const SizedBox(height: 16),
              TextField(
                controller: _distanceController,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*'))],
                decoration: const InputDecoration(
                  hintText: 'Distance in cm',
                  border: OutlineInputBorder(),
                  suffixText: 'cm',
                ),
                autofocus: true,
                onChanged: (value) => _updateSubmitStatus(),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                _resetPoints();
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                _updateSubmitStatus();
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _submitCalibration() async {
    if (!canSubmit || firstPoint == null || secondPoint == null) return;

    //Print the points
    print('Submitting calibration:');
    print('First Point: $firstPoint');
    print('Second Point: $secondPoint');

    setState(() {
      isLoading = true;
    });

    try {
      final distance = double.parse(_distanceController.text.trim());

      final rooms = await _calibrationService.submitCalibrationData(
        buildingId: widget.building.buildingId,
        buildingFloor: widget.floor,
        firstPoint: firstPoint!,
        secondPoint: secondPoint!,
        northOffset: pdrNorthOffset,
        distanceInCm: distance,
      );

      setState(() {
        isLoading = false;
      });

      if (rooms.isNotEmpty) {
        _showSuccessDialog();
      } else {
        _showErrorDialog('Failed to submit calibration data. Please try again.');
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      print('Error submitting calibration: $e');
      _showErrorDialog('An error occurred while submitting. Please try again.');
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Success!'),
          content: const Text('Calibration data has been successfully submitted.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AdminFloorView(building: widget.building,selectedFloor: widget.floor,),
                  ),
                );
              },
              child: const Text('Done'),
            ),
          ],
        );
      },
    );
  }

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Error'),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  Widget _buildInstructions() {
    String instruction;
    IconData icon;
    Color color;

    if (isNavigateMode) {
      instruction = 'Navigate Mode: Zoom and pan the floor plan. Switch to Calibrate mode to set points.';
      icon = Icons.pan_tool;
      color = Colors.blue;
    } else if (firstPoint == null) {
      instruction = 'Calibrate Mode: Tap on the floor plan to set the first point';
      icon = Icons.touch_app;
      color = Colors.orange;
    } else if (secondPoint == null) {
      instruction = 'Calibrate Mode: Tap on the floor plan to set the second point';
      icon = Icons.touch_app;
      color = Colors.orange;
    } else {
      instruction = 'Enter the distance and click Done to submit';
      icon = Icons.rule;
      color = Colors.green;
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      color: Colors.blue.shade50,
      child: Column(
        children: [
          // Mode toggle buttons
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: isNavigateMode ? null : _toggleMode,
                  icon: const Icon(Icons.pan_tool),
                  label: const Text('Navigate'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isNavigateMode ? Colors.blue : Colors.grey.shade300,
                    foregroundColor: isNavigateMode ? Colors.white : Colors.grey.shade600,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: isNavigateMode ? _toggleMode : null,
                  icon: const Icon(Icons.touch_app),
                  label: const Text('Calibrate'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: !isNavigateMode ? Colors.orange : Colors.grey.shade300,
                    foregroundColor: !isNavigateMode ? Colors.white : Colors.grey.shade600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Instruction text
          Row(
            children: [
              Icon(icon, color: Colors.blue.shade700),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  instruction,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.blue.shade700,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              if (firstPoint != null && !isNavigateMode)
                TextButton(
                  onPressed: _resetPoints,
                  child: const Text('Reset'),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPointMarker(Offset point, Color color, String label) {
    return Positioned(
      left: point.dx - 15/2,
      top: point.dy - 15/2,
      child: Container(
        width: 15,
        height: 15,
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.8),
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
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 6,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLine() {
    if (firstPoint == null || secondPoint == null) return const SizedBox.shrink();

    return CustomPaint(
      painter: LinePainter(firstPoint!, secondPoint!),
      child: Container(),
    );
  }

  Widget _buildSvgWithOverlay() {
    return LayoutBuilder(
      builder: (context, constraints) {
        return InteractiveViewer(
          transformationController: _transformationController,
          boundaryMargin: const EdgeInsets.all(20),
          minScale: 0.3,
          maxScale: 5.0,
          constrained: false,
          // Only enable interaction when in navigate mode
          panEnabled: isNavigateMode,
          scaleEnabled: isNavigateMode,
          child: GestureDetector(
            // Only detect taps when in calibrate mode
            onTapDown: isNavigateMode ? null : _onSvgTap,
            behavior: HitTestBehavior.translucent,
            child: Container(
              width: constraints.maxWidth > 800 ? constraints.maxWidth : 800,
              height: constraints.maxHeight > 800 ? constraints.maxHeight : 800,
              child: Stack(
                clipBehavior: Clip.none,
                children: [
                  // SVG Background - Center it in the container
                  Center(
                    child: SizedBox(
                      width: 800,
                      height: 800,
                      child: SvgPicture.string(
                        svgData!,
                        fit: BoxFit.contain,
                      ),
                    ),
                  ),
                  // Line between points
                  _buildLine(),
                  // Point markers
                  if (firstPoint != null)
                    _buildPointMarker(firstPoint!, Colors.blue, '1'),
                  if (secondPoint != null)
                    _buildPointMarker(secondPoint!, Colors.red, '2'),
                  // Mode indicator overlay
                  //if (!isNavigateMode)
                    // Positioned(
                    //   top: 20,
                    //   right: 20,
                    //   child: Container(
                    //     padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    //     decoration: BoxDecoration(
                    //       color: Colors.orange.withValues(alpha: 0.9),
                    //       borderRadius: BorderRadius.circular(20),
                    //       boxShadow: [
                    //         BoxShadow(
                    //           color: Colors.black.withOpacity(0.3),
                    //           blurRadius: 4,
                    //           offset: const Offset(0, 2),
                    //         ),
                    //       ],
                    //     ),
                    //     child: const Row(
                    //       mainAxisSize: MainAxisSize.min,
                    //       children: [
                    //         Icon(Icons.touch_app, color: Colors.white, size: 16),
                    //         SizedBox(width: 4),
                    //         Text(
                    //           'CALIBRATE MODE',
                    //           style: TextStyle(
                    //             color: Colors.white,
                    //             fontSize: 12,
                    //             fontWeight: FontWeight.bold,
                    //           ),
                    //         ),
                    //       ],
                    //     ),
                    //   ),
                    // ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _showNorthAlignmentDialog() async {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        return NorthAlignmentDialog(
          initialOffset: pdrNorthOffset,
          onOffsetChanged: (newOffset) {
            setState(() {
              pdrNorthOffset = newOffset;
            });
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.building.name} - Calibration'),
        centerTitle: true,
        actions: [
          if (canSubmit && !isLoading)
            IconButton(
              onPressed: _submitCalibration,
              icon: const Icon(Icons.check_circle, color: Colors.green),
            ),
        ],
      ),
      body: Column(
        children: [
          _buildInstructions(),
          Expanded(
            child: isLoading
                ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Loading...'),
                ],
              ),
            )
                : svgData == null
                ? const Center(
              child: Text('Failed to load floor plan'),
            )
                : _buildSvgWithOverlay(),
          ),
        ],
      ),
      floatingActionButton: canSubmit && !isLoading
          ? FloatingActionButton.extended(
        onPressed: _submitCalibration,
        icon: const Icon(Icons.done),
        label: const Text('Done'),
        backgroundColor: Colors.green,
      )
          : null,
    );
  }
}

class LinePainter extends CustomPainter {
  final Offset start;
  final Offset end;

  LinePainter(this.start, this.end);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.orange
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;

    canvas.drawLine(start, end, paint);

    // Draw distance text at the middle of the line
    final midPoint = Offset(
      (start.dx + end.dx) / 2,
      (start.dy + end.dy) / 2,
    );

    final distance = ((end - start).distance).toStringAsFixed(1);
    final textPainter = TextPainter(
      text: TextSpan(
        text: '${distance}px',
        style: const TextStyle(
          color: Colors.orange,
          fontSize: 12,
          fontWeight: FontWeight.bold,
          backgroundColor: Colors.white,
        ),
      ),
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();
    textPainter.paint(
      canvas,
      Offset(
        midPoint.dx - textPainter.width / 2,
        midPoint.dy - textPainter.height / 2,
      ),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}


