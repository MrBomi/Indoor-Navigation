import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';
import '../../models/Building.dart';
import 'package:indigo_test/screens/user/navigate_screen.dart';

class BuildingCard extends StatefulWidget {
  final Building building;
  final VoidCallback? onTap; // Nullable in case it's optional
  final Function(Building, bool)? onFavoriteToggle; // Callback for favorite toggle

  const BuildingCard({
    super.key,
    required this.building,
    this.onTap,
    this.onFavoriteToggle,
  });

  @override
  State<BuildingCard> createState() => _BuildingCardState();
}

class _BuildingCardState extends State<BuildingCard> {
  bool isLoadingFavorite = false;

  void _toggleFavorite() async {
    if (isLoadingFavorite) return; // Prevent multiple taps while loading

    setState(() {
      isLoadingFavorite = true;
    });

    try {
      // Toggle the favorite state optimistically
      final newFavoriteState = !widget.building.isFavorite;

      // Call the callback to handle the server request
      if (widget.onFavoriteToggle != null) {
        await widget.onFavoriteToggle!(widget.building, newFavoriteState);
      }

      // Update the building's favorite state
      setState(() {
        widget.building.isFavorite = newFavoriteState;
      });
    } catch (e) {
      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to update favorite: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        isLoadingFavorite = false;
      });
    }
  }

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
              builder: (context) => UserFloorView(building: widget.building,),
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
            widget.building.name,
            style: TextStyle(fontWeight: FontWeight.bold)
        ),
        subtitle: Text(widget.building.address),
        trailing: GestureDetector(
          onTap: _toggleFavorite,
          child: Container(
            padding: EdgeInsets.all(8),
            child: isLoadingFavorite
                ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).primaryColor,
                ),
              ),
            )
                : Icon(
              widget.building.isFavorite
                  ? Icons.star
                  : Icons.star_border,
              color: widget.building.isFavorite
                  ? Colors.amber
                  : Colors.grey,
              size: 28,
            ),
          ),
        ),
      ),
    );
  }
}