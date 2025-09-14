import 'dart:math';
import 'package:flutter/material.dart';

class NorthAlignmentDialog extends StatefulWidget {
  final double initialOffset;
  final Function(double) onOffsetChanged;

  const NorthAlignmentDialog({
    Key? key,
    required this.initialOffset,
    required this.onOffsetChanged,
  }) : super(key: key);

  @override
  State<NorthAlignmentDialog> createState() => _NorthAlignmentDialogState();
}

class _NorthAlignmentDialogState extends State<NorthAlignmentDialog> {
  late double _tempOffset;

  @override
  void initState() {
    super.initState();
    _tempOffset = widget.initialOffset;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Align North Direction'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Rotate the adjustment to align the arrow with the north direction on your floor map.',
            style: TextStyle(fontSize: 14),
          ),
          const SizedBox(height: 20),

          // Compass visualization
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey.shade300, width: 2),
              shape: BoxShape.circle,
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Background circle
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    shape: BoxShape.circle,
                  ),
                ),
                // North arrow
                Transform.rotate(
                  angle: _tempOffset * pi / 180.0,
                  child: const Icon(
                    Icons.navigation,
                    size: 40,
                    color: Colors.red,
                  ),
                ),
                // N, E, S, W labels
                const Positioned(top: 8, child: Text('N', style: TextStyle(fontWeight: FontWeight.bold))),
                const Positioned(right: 8, child: Text('E', style: TextStyle(fontWeight: FontWeight.bold))),
                const Positioned(bottom: 8, child: Text('S', style: TextStyle(fontWeight: FontWeight.bold))),
                const Positioned(left: 8, child: Text('W', style: TextStyle(fontWeight: FontWeight.bold))),
              ],
            ),
          ),

          const SizedBox(height: 20),

          // Slider for adjustment
          Text('Adjustment: ${_tempOffset.toStringAsFixed(0)}°'),
          Slider(
            value: _tempOffset,
            min: -180,
            max: 180,
            divisions: 72,
            label: '${_tempOffset.toStringAsFixed(0)}°',
            onChanged: (value) {
              setState(() {
                _tempOffset = value;
              });
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            widget.onOffsetChanged(_tempOffset);
            Navigator.of(context).pop();
          },
          child: const Text('Apply'),
        ),
      ],
    );
  }
}