import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

class FloorPickerButton extends StatelessWidget {
  final int selectedFloor;
  final List<int> floorsList;
  final ValueChanged<int> onFloorSelected;

  const FloorPickerButton({
    super.key,
    required this.floorsList,
    required this.selectedFloor,
    required this.onFloorSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      // disable the button if there's nothing to pick
      onPressed: floorsList.isEmpty ? null : () => _showFloorPicker(context),
      child: Text('Select Floor: $selectedFloor'),
    );
  }

  void _showFloorPicker(BuildContext context) {
    // safety check—shouldn't happen since button is disabled, but just in case
    if (floorsList.isEmpty) return;

    // find index of the selectedFloor, default to 0 if missing or out of bounds
    int initialIndex = floorsList.indexOf(selectedFloor);
    if (initialIndex < 0 || initialIndex >= floorsList.length) {
      initialIndex = 0;
    }
    int tempIndex = initialIndex;

    showModalBottomSheet(
      context: context,
      builder: (_) {
        return SizedBox(
          height: 250,
          child: Column(
            children: [
              // Done toolbar
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    child: const Text('Done'),
                    onPressed: () {
                      Navigator.pop(context);
                      onFloorSelected(floorsList[tempIndex]);
                    },
                  ),
                ],
              ),

              // The picker itself
              Expanded(
                child: CupertinoPicker(
                  scrollController:
                  FixedExtentScrollController(initialItem: initialIndex),
                  itemExtent: 40,
                  onSelectedItemChanged: (index) {
                    tempIndex = index;
                  },
                  children: floorsList
                      .map((floor) => Center(child: Text('Floor $floor')))
                      .toList(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
