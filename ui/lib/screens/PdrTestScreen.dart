import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:flutter_compass/flutter_compass.dart';

class PdrTestScreen extends StatefulWidget {
  const PdrTestScreen({super.key});

  @override
  State<PdrTestScreen> createState() => _PdrTestScreenState();
}

class _PdrTestScreenState extends State<PdrTestScreen> {
  // World-frame pose: (0,0) at start. Y+ = North (up), X+ = East (right).
  double xMeters = 0.0;
  double yMeters = 0.0;

  // Heading: 0° = North, 90° = East, 180° = South, 270° = West
  double? headingDeg;

  // Step logic
  int steps = 0;
  double stepLengthMeters = 0.70;   // tweak per user
  final int minStepIntervalMs = 250;
  int _lastStepMs = 0;

  // Simple step detection on userAccelerometer magnitude (gravity removed)
  StreamSubscription? _accSub;
  StreamSubscription? _compassSub;
  double _emaMag = 0.0;             // smoothed magnitude
  final double _smoothAlpha = 0.2;  // 0..1 (higher = faster response)
  final double _stepThreshold = 1.2; // m/s^2 (tune)
  double _prevEmaMag = 0.0;
  bool _running = false;

  // Path history in meters (world frame). Start at origin.
  List<Offset> _path = [Offset.zero];

  // ---- NEW: adaptive scale (pixels per meter) that only shrinks when needed
  final ValueNotifier<double> _scalePxPerMeter = ValueNotifier<double>(60.0);
  static const double _minScalePxPerMeter = 10.0;  // don't go smaller than this
  static const double _maxScalePxPerMeter = 200.0; // not used for growing in this demo
  static const double _paddingPx = 16.0;

  @override
  void dispose() {
    _stop();
    super.dispose();
  }

  void _start() {
    if (_running) return;
    _running = true;

    // 1) Compass heading (degrees from magnetic north)
    _compassSub = FlutterCompass.events?.listen((event) {
      setState(() {
        headingDeg = event.heading; // can be null if sensor not available
      });
    });

    // 2) Accelerometer without gravity -> step detection
    _accSub = userAccelerometerEventStream().listen((e) {
      final nowMs = DateTime.now().millisecondsSinceEpoch;

      // magnitude of linear acceleration (m/s^2)
      final mag = sqrt(e.x * e.x + e.y * e.y + e.z * e.z);

      // smooth with EMA
      _emaMag = (1 - _smoothAlpha) * _emaMag + _smoothAlpha * mag;

      // rising-edge detection across threshold with min interval (debounce)
      final bool rising = _prevEmaMag <= _stepThreshold && _emaMag > _stepThreshold;
      final bool spaced = (nowMs - _lastStepMs) > minStepIntervalMs;

      if (rising && spaced) {
        _lastStepMs = nowMs;
        steps += 1;

        final double hdg = (headingDeg ?? 0.0) * pi / 180.0; // radians
        // Advance in the direction of heading:
        // X+ = East = sin(heading), Y+ = North = cos(heading)
        xMeters += stepLengthMeters * sin(hdg);
        yMeters += stepLengthMeters * cos(hdg);

        // Append new point to the path (in meters)
        _path.add(Offset(xMeters, yMeters));

        if (mounted) setState(() {});
      }

      _prevEmaMag = _emaMag;
    });

    setState(() {});
  }

  void _stop() {
    _running = false;
    _accSub?.cancel();
    _accSub = null;
    _compassSub?.cancel();
    _compassSub = null;
    setState(() {});
  }

  void _reset() {
    steps = 0;
    xMeters = 0;
    yMeters = 0;
    _lastStepMs = 0;
    _emaMag = 0;
    _prevEmaMag = 0;
    _path = [Offset.zero];
    _scalePxPerMeter.value = 60.0; // reset default scale
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final mono = const TextStyle(fontFamily: 'RobotoMono', fontSize: 18, height: 1.2);
    final big = mono.copyWith(fontSize: 22, fontWeight: FontWeight.w600);

    return Scaffold(
      appBar: AppBar(
        title: const Text('PDR Test: Live X/Y + Path (auto-shrink)'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Live numbers
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Position (meters):', style: big),
                    const SizedBox(height: 8),
                    Text('X (East + / West -): ${xMeters.toStringAsFixed(2)}', style: mono),
                    Text('Y (North + / South -): ${yMeters.toStringAsFixed(2)}', style: mono),
                    const SizedBox(height: 12),
                    Text('Heading: ${headingDeg?.toStringAsFixed(1) ?? "—"}°  (0°=N, 90°=E)', style: mono),
                    Text('Steps: $steps', style: mono),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 12),

            // Controls
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: Icon(_running ? Icons.pause : Icons.play_arrow),
                    label: Text(_running ? 'Stop' : 'Start'),
                    onPressed: _running ? _stop : _start,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reset (0,0)'),
                    onPressed: _reset,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Step length tuner
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      children: [
                        const Text('Step length (m)'),
                        const Spacer(),
                        Text(stepLengthMeters.toStringAsFixed(2)),
                      ],
                    ),
                    Slider(
                      min: 0.4,
                      max: 0.9,
                      divisions: 25,
                      value: stepLengthMeters,
                      label: stepLengthMeters.toStringAsFixed(2),
                      onChanged: (v) => setState(() => stepLengthMeters = v),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 12),

            // PATH CANVAS with auto-shrinking scale
            Expanded(
              child: Card(
                clipBehavior: Clip.antiAlias,
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final size = Size(constraints.maxWidth, constraints.maxHeight);
                    return ValueListenableBuilder<double>(
                      valueListenable: _scalePxPerMeter,
                      builder: (_, scale, __) {
                        return CustomPaint(
                          painter: _PathPainter(
                            points: _path,
                            headingDeg: headingDeg,
                            scalePxPerMeter: scale,
                            paddingPx: _paddingPx,
                            onRequireSmallerScale: (double requiredScale) {
                              // Only shrink, never grow
                              final newScale = requiredScale.clamp(
                                _minScalePxPerMeter,
                                _scalePxPerMeter.value,
                              );
                              if (newScale < _scalePxPerMeter.value) {
                                // Update after frame to avoid setState during paint
                                WidgetsBinding.instance.addPostFrameCallback((_) {
                                  _scalePxPerMeter.value = newScale;
                                });
                              }
                            },
                            canvasSize: size,
                          ),
                          child: const SizedBox.expand(),
                        );
                      },
                    );
                  },
                ),
              ),
            ),

            const SizedBox(height: 8),
            const Text(
              'Origin (0,0) at center. If the path reaches the rectangle boundary, the scale auto-shrinks to keep it inside.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _PathPainter extends CustomPainter {
  final List<Offset> points;   // in meters
  final double? headingDeg;
  final double scalePxPerMeter;     // current scale (px per meter)
  final double paddingPx;           // inner padding
  final Size canvasSize;
  final void Function(double requiredScale) onRequireSmallerScale;

  _PathPainter({
    required this.points,
    required this.headingDeg,
    required this.scalePxPerMeter,
    required this.paddingPx,
    required this.canvasSize,
    required this.onRequireSmallerScale,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);

    // --- Check if current scale fits all points; if not, request a smaller one.
    double maxX = 0, maxY = 0;
    for (final p in points) {
      if (p.dx.abs() > maxX) maxX = p.dx.abs();
      if (p.dy.abs() > maxY) maxY = p.dy.abs();
    }

    // If we have movement, compute the *maximum allowed* scale that still fits
    if (maxX > 0 || maxY > 0) {
      final maxScaleX = (size.width / 2 - paddingPx) / (maxX == 0 ? 1 : maxX);
      final maxScaleY = (size.height / 2 - paddingPx) / (maxY == 0 ? 1 : maxY);
      final maxAllowedScale = max(0.0, min(maxScaleX, maxScaleY));
      if (scalePxPerMeter > maxAllowedScale && maxAllowedScale > 0) {
        // Ask the state to shrink to maxAllowedScale (or smaller).
        onRequireSmallerScale(maxAllowedScale);
      }
    }

    // Helper: world(m) -> canvas(px), remembering Y+ is UP
    Offset mapPt(Offset m) => Offset(
      center.dx + m.dx * scalePxPerMeter,
      center.dy - m.dy * scalePxPerMeter,
    );

    // Background
    final bg = Paint()..color = const Color(0xFFF8F9FB);
    canvas.drawRect(Offset.zero & size, bg);

    // Axes
    final axis = Paint()
      ..color = Colors.grey.shade400
      ..strokeWidth = 1.0;
    canvas.drawLine(Offset(0, center.dy), Offset(size.width, center.dy), axis);  // X axis
    canvas.drawLine(Offset(center.dx, 0), Offset(center.dx, size.height), axis);  // Y axis

    // Grid (approx 1 m lines; keep >= 40 px apart)
    final grid = Paint()
      ..color = Colors.grey.shade200
      ..strokeWidth = 1.0;
    final gridStepPx = max(40.0, scalePxPerMeter); // at least 40 px
    for (double x = center.dx; x < size.width; x += gridStepPx) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    }
    for (double x = center.dx; x > 0; x -= gridStepPx) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    }
    for (double y = center.dy; y < size.height; y += gridStepPx) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }
    for (double y = center.dy; y > 0; y -= gridStepPx) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    // Path
    if (points.isNotEmpty) {
      final pathPaint = Paint()
        ..color = Colors.blue
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.0
        ..strokeCap = StrokeCap.round
        ..strokeJoin = StrokeJoin.round;

      final p = Path();
      final first = mapPt(points.first);
      p.moveTo(first.dx, first.dy);
      for (int i = 1; i < points.length; i++) {
        final pt = mapPt(points[i]);
        p.lineTo(pt.dx, pt.dy);
      }
      canvas.drawPath(p, pathPaint);

      // Current position dot
      final curr = mapPt(points.last);
      canvas.drawCircle(curr, 5.5, Paint()..color = Colors.red);
    }

    // North arrow (top-right corner)
    if (headingDeg != null) {
      final arrowCenter = Offset(size.width - 36, 36);
      final r = 14.0;
      final ring = Paint()
        ..color = Colors.black.withOpacity(0.06)
        ..style = PaintingStyle.fill;
      canvas.drawCircle(arrowCenter, 18, ring);

      final hdgRad = headingDeg! * pi / 180.0;
      // Arrow pointing to North = up (0°)
      final tip = arrowCenter + Offset(0, -r);
      final rot = Matrix4.identity()
        ..translate(arrowCenter.dx, arrowCenter.dy)
        ..rotateZ(hdgRad)
        ..translate(-arrowCenter.dx, -arrowCenter.dy);
      canvas.save();
      canvas.transform(rot.storage);
      final arrow = Paint()
        ..color = Colors.black87
        ..strokeWidth = 2.0
        ..style = PaintingStyle.stroke;
      // simple up arrow
      canvas.drawLine(arrowCenter + Offset(0, r), arrowCenter + Offset(0, -r), arrow);
      canvas.drawLine(arrowCenter + Offset(-6, -r + 8), tip, arrow);
      canvas.drawLine(arrowCenter + Offset(6, -r + 8), tip, arrow);
      canvas.restore();
    }
  }

  @override
  bool shouldRepaint(covariant _PathPainter oldDelegate) {
    return oldDelegate.points != points ||
        oldDelegate.headingDeg != headingDeg ||
        oldDelegate.scalePxPerMeter != scalePxPerMeter ||
        oldDelegate.canvasSize != canvasSize;
  }
}
