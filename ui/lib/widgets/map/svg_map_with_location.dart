import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../models/user_location.dart';
import 'animated_location_dot.dart';

class SvgMapWithLocation extends StatefulWidget {
  final String svgData;
  final double svgWidth;
  final double svgHeight;
  final UserLocation? userLocation;

  const SvgMapWithLocation({
    Key? key,
    required this.svgData,
    required this.svgWidth,
    required this.svgHeight,
    this.userLocation,
  }) : super(key: key);

  @override
  State<SvgMapWithLocation> createState() => _SvgMapWithLocationState();
}

class _SvgMapWithLocationState extends State<SvgMapWithLocation> {
  final TransformationController _transformationController =
  TransformationController();

  @override
  Widget build(BuildContext context) {
    return InteractiveViewer(
      transformationController: _transformationController,
      boundaryMargin: const EdgeInsets.all(20),
      minScale: 0.1,
      maxScale: 5.0,
      constrained: false,
      child: SizedBox(
        width: widget.svgWidth,
        height: widget.svgHeight,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            SvgPicture.string(
              widget.svgData,
              width: widget.svgWidth,
              height: widget.svgHeight,
              fit: BoxFit.fill,
            ),
            if (widget.userLocation != null)
              Positioned(
                left: widget.userLocation!.x - 12,
                top: widget.userLocation!.y - 12,
                child: const AnimatedLocationDot(),
              ),
          ],
        ),
      ),
    );
  }
}