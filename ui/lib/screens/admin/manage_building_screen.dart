import 'package:flutter/material.dart';
import 'package:indigo_test/services/admin/admin_service.dart';
import '../../models/Building.dart';
import 'add_new_building.dart';
import 'admin_building_card.dart';


class ManageBuildingsPage extends StatefulWidget {
  const ManageBuildingsPage({super.key});

  @override
  State<ManageBuildingsPage> createState() => _ManageBuildingsPageState();
}

class _ManageBuildingsPageState extends State<ManageBuildingsPage> {
  List<Building> buildings = [];
  bool isLoading = true; // Track loading state

  @override
  void initState() {
    super.initState();
    _loadBuildings();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.only(top:16,bottom: 16, left: 6, right: 6),
          child: Column(
            children: [
              _buildTopPanel(context),
              const SizedBox(height: 16),
              _buildExistingBuildingsLabel(),
              const SizedBox(height: 10),
              _buildContent(),
              const SizedBox(height: 16),
              _buildAddButton(context),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _loadBuildings() async {
    setState(() {
      isLoading = true;
    });

    try {
      final result = await AdminService().getUserBuildings();
      setState(() {
        buildings = result;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        buildings = [];
        isLoading = false;
      });
      print('Error loading buildings: $e');
    }
  }

  Widget _buildTopPanel(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        const Text(
          'Manage Buildings',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        IconButton(
          icon: const Icon(Icons.settings),
          onPressed: () {
            // TODO: Handle settings button tap
          },
        ),
      ],
    );
  }

  Widget _buildExistingBuildingsLabel() {
    return const Align(
      alignment: Alignment.centerLeft,
      child: Text(
        'Existing Buildings',
        style: TextStyle(
          fontSize: 12,
          color: Color(0xFF7F7F7F),
        ),
      ),
    );
  }

  // Main content area that switches between loading, empty, and list states
  Widget _buildContent() {
    return Expanded(
      child: isLoading
          ? _buildLoadingState()
          : buildings.isEmpty
          ? _buildEmptyState()
          : _buildBuildingList(),
    );
  }

  // Loading state
  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            strokeWidth: 3,
            valueColor: AlwaysStoppedAnimation<Color>(
              Theme.of(context).primaryColor,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Loading Buildings...',
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  // Empty state when no buildings
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.business_outlined,
            size: 80,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            'No Buildings Found',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'You haven\'t created any buildings yet.\nTap the button below to add your first building.',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[500],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildBuildingList() {
    return ListView.builder(
        itemCount: buildings.length,
        itemBuilder: (context, index) {
          final building = buildings[index];
          return AdminBuildingCard(building: building);
        }
    );
  }

  Widget _buildAddButton(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF225FFF),
          foregroundColor: Colors.white,
        ),
        onPressed: () => _handleAddBuilding(context),
        child: const Text('+ Add New Building'),
      ),
    );
  }

  Future<void> _handleAddBuilding(BuildContext context) async {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const AddNewBuildingScreen(),
      ),
    ).then((status) {
      if (status == 201) {
        // Handle the newly created building
        // Add it to your buildings list and refresh UI
        _loadBuildings();
      }
    });
  }
}