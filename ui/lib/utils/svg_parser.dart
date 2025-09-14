import 'package:xml/xml.dart';

class SvgParser {
  static SvgDimensions parseDimensions(String svgString) {
    try {
      final document = XmlDocument.parse(svgString);
      final svgElement = document.findAllElements('svg').first;

      final widthAttr = svgElement.getAttribute('width');
      final heightAttr = svgElement.getAttribute('height');

      if (widthAttr != null && heightAttr != null) {
        final widthStr = widthAttr.replaceAll(RegExp(r'[^0-9.]'), '');
        final heightStr = heightAttr.replaceAll(RegExp(r'[^0-9.]'), '');

        final width = double.tryParse(widthStr) ?? 800;
        final height = double.tryParse(heightStr) ?? 800;

        return SvgDimensions(width: width, height: height);
      } else {
        final viewBox = svgElement.getAttribute('viewBox');
        if (viewBox != null) {
          final parts = viewBox.split(' ');
          if (parts.length == 4) {
            final width = double.tryParse(parts[2]) ?? 800;
            final height = double.tryParse(parts[3]) ?? 800;
            return SvgDimensions(width: width, height: height);
          }
        }
      }

      return const SvgDimensions(width: 800, height: 800);
    } catch (e) {
      print('Error parsing SVG dimensions: $e');
      return const SvgDimensions(width: 800, height: 800);
    }
  }
}

class SvgDimensions {
  final double width;
  final double height;

  const SvgDimensions({
    required this.width,
    required this.height,
  });
}