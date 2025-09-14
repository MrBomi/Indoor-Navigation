import 'package:flutter/material.dart';
import 'package:indigo_test/services/user/home_screen_service.dart';
import '../../main.dart';
import '../../models/Building.dart';
import '../../services/user/favorite_service.dart';
import '../../widgets/google_map.dart';
import '../../widgets/bottom_menu_bar.dart';
import '../user/building_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with RouteAware {
  List<Building> buildings = [];
  List<Building> favoriteBuildings = [];
  int _currentIndex = 0;
  bool isLoading = true;
  final FavoriteService _favoriteService = FavoriteService();

  @override
  void initState() {
    super.initState();
    _loadBuildings();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    routeObserver.subscribe(this, ModalRoute.of(context)!);
  }

  @override
  void dispose() {
    routeObserver.unsubscribe(this);
    super.dispose();
  }

  @override
  void didPopNext() {
    _loadBuildings();
  }

  Future<void> _loadBuildings() async {
    setState(() => isLoading = true);
    try {
      final result = await HomeService().getAllBuildings();
      final favorites = await _favoriteService.getFavoriteBuildings();
      for (var b in result) {
        b.isFavorite = favorites.any((f) => f.buildingId == b.buildingId);
      }
      setState(() {
        buildings = result;
        favoriteBuildings = favorites;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        buildings = [];
        favoriteBuildings = [];
        isLoading = false;
      });
      print('Error loading buildings: $e');
    }
  }

  Future<void> _handleFavoriteToggle(Building building, bool isFavorite) async {
    try {
      await _favoriteService.toggleFavorite(building, isFavorite);
      setState(() {
        if (isFavorite) {
          if (!favoriteBuildings.any((f) => f.buildingId == building.buildingId)) {
            favoriteBuildings.add(building);
          }
        } else {
          favoriteBuildings.removeWhere((f) => f.buildingId == building.buildingId);
        }
      });
    } catch (e) {
      rethrow;
    }
  }

  void _onTabTapped(int i) => setState(() => _currentIndex = i);

  Widget _buildHomeContent() {
    return Column(
      children: [
        TopBar(),
        Expanded(
          child: isLoading
              ? _buildLoadingState()
              : buildings.isEmpty
              ? _buildEmptyState()
              : _buildBuildingList(),
        ),
      ],
    );
  }

  Widget _buildMapContent() {
    return Column(
      children: [
        TopBar(),
        Expanded(child: MapPage()),
      ],
    );
  }

  Widget _buildFavoritesContent() {
    return Column(
      children: [
        TopBar(),
        Expanded(
          child: favoriteBuildings.isEmpty
              ? _buildEmptyFavoritesState()
              : _buildFavoritesList(),
        ),
      ],
    );
  }

  Widget _buildEmptyFavoritesState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.star_outline, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text('No Favorite Buildings',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.grey[600])),
          const SizedBox(height: 8),
          Text(
            'Tap the star icon on any building\nto add it to your favorites.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildFavoritesList() {
    return ListView.builder(
      padding: const EdgeInsets.all(8.0),
      itemCount: favoriteBuildings.length,
      itemBuilder: (ctx, idx) {
        return BuildingCard(
          building: favoriteBuildings[idx],
          onFavoriteToggle: _handleFavoriteToggle,
        );
      },
    );
  }

  // ← This was missing!
  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            strokeWidth: 3,
            valueColor: AlwaysStoppedAnimation<Color>(Theme.of(context).primaryColor),
          ),
          const SizedBox(height: 24),
          Text(
            'Loading Buildings...',
            style: TextStyle(fontSize: 18, color: Colors.grey[600], fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.business_outlined, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text('No Buildings in the System',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.grey[600])),
          const SizedBox(height: 8),
          Text(
            'There are currently no buildings available.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildBuildingList() {
    return ListView.builder(
      padding: const EdgeInsets.all(8.0),
      itemCount: buildings.length,
      itemBuilder: (ctx, idx) {
        return BuildingCard(
          building: buildings[idx],
          onFavoriteToggle: _handleFavoriteToggle,
        );
      },
    );
  }

  Widget _getCurrentTabContent() {
    switch (_currentIndex) {
      case 1:
        return _buildMapContent();
      case 2:
        return _buildFavoritesContent();
      case 0:
      default:
        return _buildHomeContent();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(child: _getCurrentTabContent()),
      bottomNavigationBar: BottomNavBar(
        selectedIndex: _currentIndex,
        onTabTapped: _onTabTapped,
      ),
    );
  }
}
