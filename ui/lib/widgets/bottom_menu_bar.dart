import 'package:flutter/material.dart';
import 'package:flutter_svg/svg.dart';
import '../screens/admin/manage_building_screen.dart';

class BottomNavBar extends StatefulWidget {
  final int selectedIndex; // Add this parameter
  final Function(int) onTabTapped; // Add this callback

  const BottomNavBar({
    super.key,
    this.selectedIndex = 0,
    required this.onTabTapped,
  });

  @override
  _BottomNavBarState createState() => _BottomNavBarState();
}

class _BottomNavBarState extends State<BottomNavBar> {
  void _onItemTapped(int index) {
    widget.onTabTapped(index); // Call the parent callback
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          height: 64,
          margin: const EdgeInsets.symmetric(horizontal: 40),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(30),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                offset: Offset(0, 5),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(30),
            child: BottomNavigationBar(
              type: BottomNavigationBarType.fixed,
              backgroundColor: Colors.transparent,
              elevation: 0,
              currentIndex: widget.selectedIndex, // Use the passed index
              onTap: _onItemTapped,
              selectedItemColor: Theme.of(context).primaryColor,
              unselectedItemColor: Colors.grey,
              showSelectedLabels: true,
              showUnselectedLabels: false,
              iconSize: 26,
              items: const [
                BottomNavigationBarItem(icon: Icon(Icons.home), label: "Home"),
                BottomNavigationBarItem(icon: Icon(Icons.map), label: "Map"),
                BottomNavigationBarItem(icon: Icon(Icons.star), label: "Favorites"),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class TopBar extends StatelessWidget {
  const TopBar({super.key});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: _buildAvatar(),
      title: _buildTitle(),
      subtitle: _buildSubtitle("Noam Kontorovich"),
      trailing: _buildTrailing(context),
    );
  }

  Widget _buildAvatar() {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white,
        border: Border.all(
          color: Colors.grey.shade800,
          width: 1.5,
        ),
      ),
      child: Center(
        child: SvgPicture.asset(
          'assets/icons/man_with_map.svg',
          width: 48,
          height: 48,
          fit: BoxFit.cover,
        ),
      ),
    );
  }

  Widget _buildTitle() {
    return const Text(
      "Hi, Welcome Back",
      style: TextStyle(fontSize: 14),
    );
  }

  Widget _buildSubtitle(String userName) {
    return Text(
      userName,
      style: TextStyle(fontWeight: FontWeight.bold),
    );
  }

  Widget _buildTrailing(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const SizedBox(width: 10),
        IconButton(
          icon: const Icon(Icons.more_vert),
          tooltip: 'More options',
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const ManageBuildingsPage(),
              ),
            );
          },
        ),
      ],
    );
  }
}