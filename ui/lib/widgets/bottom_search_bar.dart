import 'package:flutter/material.dart';

class CustomSearchBar extends StatefulWidget {
  final List<String> allSuggestions;
  final String hintText;
  final IconData pinIcon;
  final void Function(String)? onSuggestionSelected;
  final void Function(String)? onTextChanged;

  const CustomSearchBar({
    super.key,
    required this.allSuggestions,
    required this.hintText,
    required this.pinIcon,
    this.onSuggestionSelected,
    this.onTextChanged,
  });

  @override
  State<CustomSearchBar> createState() => _CustomSearchBarState();
}

class _CustomSearchBarState extends State<CustomSearchBar> {
  final TextEditingController _textController = TextEditingController();

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(8), // Reduced padding for wider bar
      child: _buildSearchContainer(context),
    );
  }

  Widget _buildSearchContainer(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12), // Increased padding
      decoration: _containerDecoration(),
      child: Row(
        children: [
          _buildPinIcon(),
          const SizedBox(width: 12), // Space between pin and search
          Expanded(child: _buildAutocompleteField()),
          const SizedBox(width: 8), // Space before close icon
          GestureDetector(
            onTap: () {
              // Clear both controllers
              _textController.clear();
              debugPrint('Search cleared');
            },
            child: Icon(
              Icons.close,
              color: Colors.grey[600],
              size: 20,
            ),
          ),
        ],
      ),
    );
  }

  BoxDecoration _containerDecoration() {
    return BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(24),
      boxShadow: const [
        BoxShadow(
          color: Colors.black12,
          blurRadius: 6,
          offset: Offset(0, 2),
        ),
      ],
    );
  }

  Widget _buildAutocompleteField() {
    return Autocomplete<String>(
      optionsBuilder: (TextEditingValue value) {
        if (value.text.isEmpty) return const Iterable<String>.empty();
        return widget.allSuggestions.where(
              (s) => s.toLowerCase().contains(value.text.toLowerCase()),
        );
      },
      fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
        // Sync our controller with the autocomplete controller
        controller.addListener(() {
          if (widget.onTextChanged != null) {
            widget.onTextChanged!(controller.text);
          }
        });
        controller.addListener(() {
          if (_textController.text != controller.text) {
            _textController.value = controller.value;
          }
        });

        _textController.addListener(() {
          if (controller.text != _textController.text) {
            controller.value = _textController.value;
          }
        });

        return TextField(
          controller: controller, // Use the autocomplete's controller
          focusNode: focusNode,
          decoration: InputDecoration.collapsed(
            hintText: widget.hintText,
          ),
        );
      },
      onSelected: (selection) {
        // When a suggestion is selected, update our controller too
        _textController.text = selection;
        if (widget.onSuggestionSelected != null) {
          widget.onSuggestionSelected!(selection);
        } else {
          debugPrint('Selected: $selection');
        }
      },
    );
  }

  Widget _buildPinIcon() {
    return Container(
      padding: const EdgeInsets.all(6), // Slightly larger padding
      decoration: const BoxDecoration(
        color: Colors.blueAccent,
        shape: BoxShape.circle,
      ),
      child: Icon(
        widget.pinIcon,
        color: Colors.white,
        size: 18,
      ),
    );
  }
}