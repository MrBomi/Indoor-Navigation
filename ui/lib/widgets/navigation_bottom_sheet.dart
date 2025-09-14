import 'package:flutter/material.dart';
import 'package:indigo_test/widgets/bottom_search_bar.dart';

class NavigationBottomSheet extends StatefulWidget {
  final Function(Map<String, dynamic>)? onNavigationPressed;
  final List<String> places;

  const NavigationBottomSheet({
    Key? key,
    required this.onNavigationPressed,
    required this.places,
  }) : super(key: key);

  @override
  State<NavigationBottomSheet> createState() => _NavigationBottomSheetState();
}

class _NavigationBottomSheetState extends State<NavigationBottomSheet> {
  final DraggableScrollableController _controller = DraggableScrollableController();

  // Controllers to track text in search bars
  String _destinationText = '';
  String _currentLocationText = '';

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return DraggableScrollableSheet(
      controller: _controller,
      initialChildSize: 0.12,
      minChildSize: 0.12,
      maxChildSize: 0.35,
      builder: (context, scrollController) {
        return Padding(
          padding: EdgeInsets.only(bottom: bottomInset),
          child: _buildBottomSheetContainer(scrollController),
        );
      },
    );
  }

  Widget _buildBottomSheetContainer(ScrollController scrollController) {
    return Container(
      decoration: _buildContainerDecoration(),
      child: ListView(
        controller: scrollController,
        padding: const EdgeInsets.all(8),
        children: [
          _buildDragHandle(),
          const SizedBox(height: 6),
          _buildSearchBars(),
          const SizedBox(height: 24),
          _buildGoButton(),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  BoxDecoration _buildContainerDecoration() {
    return const BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      boxShadow: [
        BoxShadow(
          color: Colors.black12,
          blurRadius: 10,
          offset: Offset(0, -5),
        ),
      ],
    );
  }

  Widget _buildDragHandle() {
    return Center(
      child: Container(
        width: 40,
        height: 4,
        decoration: BoxDecoration(
          color: Colors.grey[300],
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  Widget _buildSearchBars() {
    return Column(
      children: [
        _buildCurrentLocationSearchBar(),
        _buildDestinationSearchBar(),
      ],
    );
  }

  Widget _buildDestinationSearchBar() {
    return CustomSearchBar(
      allSuggestions: widget.places,
      hintText: "Where do you want to go?",
      pinIcon: Icons.near_me,
      onTextChanged: (text) => _destinationText = text,
    );
  }

  Widget _buildCurrentLocationSearchBar() {
    return CustomSearchBar(
      allSuggestions: widget.places,
      hintText: "Where are you now?",
      pinIcon: Icons.my_location_outlined,
      onTextChanged: (text) => _currentLocationText = text,
    );
  }

  Widget _buildGoButton() {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton(
        onPressed: _handleGoButtonPressed,
        style: _buildGoButtonStyle(),
        child: _buildGoButtonContent(),
      ),
    );
  }

  ButtonStyle _buildGoButtonStyle() {
    return ElevatedButton.styleFrom(
      backgroundColor: const Color(0xFF4CAF50),
      foregroundColor: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(25),
      ),
    );
  }

  Widget _buildGoButtonContent() {
    return const Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.navigation, size: 20),
        SizedBox(width: 8),
        Text(
          'Go Now',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  void _handleGoButtonPressed() {
    Map<String, dynamic> navigationData = {
      'destination': _destinationText,
      'currentLocation': _currentLocationText,
    };
    if (widget.onNavigationPressed != null) {
      widget.onNavigationPressed!(navigationData);
    }

    // Animate the bottom sheet back to initial size
    _controller.animateTo(
      0.12, // Initial size
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }
}