import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(home: MapSearchScreen()));
}

// Main Screen
class MapSearchScreen extends StatefulWidget {
  @override
  _MapSearchScreenState createState() => _MapSearchScreenState();
}

class _MapSearchScreenState extends State<MapSearchScreen> {
  final TextEditingController _searchController = TextEditingController();

  final List<String> _allSuggestions = [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3",
    "Suggestion 4",
    "Suggestion 5",
  ];

  List<String> _filteredSuggestions = [];

  @override
  void initState() {
    super.initState();
    _filteredSuggestions = _allSuggestions;
    _searchController.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      if (query.isEmpty) {
        _filteredSuggestions = _allSuggestions;
      } else {
        _filteredSuggestions = _allSuggestions
            .where((s) => s.toLowerCase().contains(query))
            .toList();
      }
    });
  }

  @override
  void dispose() {
    _searchController.removeListener(_onSearchChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onSuggestionTap(String suggestion) {
    _searchController.text = suggestion;
    // You can add extra logic here, like closing keyboard, etc.
  }

  void _onGoNowPressed() {
    // Implement your navigation logic here
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Go Now pressed')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final mapHeight = screenHeight * 0.4;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            MapView(height: mapHeight),

            Expanded(
              child: Column(
                children: [
                  SearchInput(
                    controller: _searchController,
                    labelText: 'Search destination',
                  ),

                  Expanded(
                    child: SuggestionsList(
                      suggestions: _filteredSuggestions,
                      onSuggestionTap: _onSuggestionTap,
                    ),
                  ),

                  GoNowButton(onPressed: _onGoNowPressed),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// MapView widget
class MapView extends StatelessWidget {
  final double height;

  const MapView({required this.height});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      color: Colors.blueGrey[300],
      alignment: Alignment.center,
      child: Text(
        'Map View (partial)',
        style: TextStyle(fontSize: 24, color: Colors.white),
      ),
    );
  }
}

// SearchInput widget
class SearchInput extends StatelessWidget {
  final TextEditingController controller;
  final String labelText;

  const SearchInput({required this.controller, required this.labelText});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: labelText,
          border: OutlineInputBorder(),
          prefixIcon: Icon(Icons.search),
        ),
      ),
    );
  }
}

// SuggestionsList widget
class SuggestionsList extends StatelessWidget {
  final List<String> suggestions;
  final void Function(String) onSuggestionTap;

  const SuggestionsList({
    required this.suggestions,
    required this.onSuggestionTap,
  });

  @override
  Widget build(BuildContext context) {
    if (suggestions.isEmpty) {
      return Center(child: Text('No suggestions'));
    }

    return ListView.separated(
      itemCount: suggestions.length,
      separatorBuilder: (_, __) => Divider(),
      itemBuilder: (context, index) {
        final suggestion = suggestions[index];
        return ListTile(
          title: Text(suggestion),
          onTap: () => onSuggestionTap(suggestion),
        );
      },
    );
  }
}

// GoNowButton widget
class GoNowButton extends StatelessWidget {
  final VoidCallback onPressed;

  const GoNowButton({required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Colors.white,
      padding: EdgeInsets.all(16),
      child: ElevatedButton(
        onPressed: onPressed,
        child: Text('Go Now'),
      ),
    );
  }
}
