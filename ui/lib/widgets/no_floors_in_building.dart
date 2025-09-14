import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

Widget buildEmptyState() {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.business_outlined, size: 80, color: Colors.grey[400]),
        const SizedBox(height: 16),
        Text('No Floors in the Building',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.grey[600])),
        const SizedBox(height: 8),
        Text(
          'There are currently no floors available.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16, color: Colors.grey[500]),
        ),
      ],
    ),
  );
}