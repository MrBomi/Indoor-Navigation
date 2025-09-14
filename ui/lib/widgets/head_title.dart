import 'package:flutter/material.dart';

Widget headTitle(BuildContext context, String title, {bool showBackIcon = true}) {
  return SizedBox(
    height: 56,
    child: Stack(
      children: [
        if (showBackIcon)
          Align(
            alignment: Alignment.centerLeft,
            child: IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: () {
                Navigator.pop(context);
              },
            ),
          ),
        Center(
          child: Text(
            title,
            style: const TextStyle(
              color: Color(0xFF225FFF),
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    ),
  );
}

