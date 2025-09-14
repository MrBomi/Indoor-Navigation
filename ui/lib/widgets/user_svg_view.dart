import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class ZoomableSvgView extends StatelessWidget {
  final String rawSvg;

  const ZoomableSvgView({super.key, required this.rawSvg});

  // @override
  // Widget build(BuildContext context) {
  //   return Center(
  //     child: PhotoView.customChild(
  //       childSize: const Size(800, 800),
  //       backgroundDecoration: const BoxDecoration(color: Colors.white),
  //       minScale: PhotoViewComputedScale.contained * 1.0,
  //       maxScale: PhotoViewComputedScale.covered * 3.0,
  //       child: SvgPicture.string(
  //         rawSvg,
  //         width: 800,
  //         height: 800,
  //         fit: BoxFit.none,               // ✅ Prevent auto-scaling
  //         alignment: Alignment.topLeft,   // ✅ Align origin to top-left
  //       ),
  //     ),
  //   );
  // }


  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return InteractiveViewer(
          boundaryMargin: const EdgeInsets.all(100),
          minScale: 0.1,
          maxScale: 5.0,
          constrained: false,
          child: Container(
            width: constraints.maxWidth > 800 ? constraints.maxWidth : 800,
            height: constraints.maxHeight > 800 ? constraints.maxHeight : 800,
            child: Center(
              child: SizedBox(
                width: 800,
                height: 800,
                child: SvgPicture.string(
                  rawSvg,
                  fit: BoxFit.contain,
                ),
              ),
            ),
          ),
        );
      },
    );
  }

}