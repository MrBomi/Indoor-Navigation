import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:confetti/confetti.dart';

/// Show this with: await showArrivalDialog(context, destinationName: "Room 317");
Future<void> showArrivalDialog(
    BuildContext context, {
      required String destinationName,
      String? subtitle,
      VoidCallback? onPrimary,
      String primaryText = "Done",
      VoidCallback? onSecondary,
      String secondaryText = "Keep Exploring",
      bool barrierDismissible = true,
    }) {
  return showDialog(
    context: context,
    barrierDismissible: barrierDismissible,
    barrierColor: Colors.black.withOpacity(0.35),
    builder: (_) => ArrivalDialog(
      destinationName: destinationName,
      subtitle: subtitle,
      onPrimary: onPrimary,
      primaryText: primaryText,
      onSecondary: onSecondary,
      secondaryText: secondaryText,
    ),
  );
}

class ArrivalDialog extends StatefulWidget {
  final String destinationName;
  final String? subtitle;
  final VoidCallback? onPrimary;
  final String primaryText;
  final VoidCallback? onSecondary;
  final String secondaryText;

  const ArrivalDialog({
    super.key,
    required this.destinationName,
    this.subtitle,
    this.onPrimary,
    this.primaryText = "Done",
    this.onSecondary,
    this.secondaryText = "Keep Exploring",
  });

  @override
  State<ArrivalDialog> createState() => _ArrivalDialogState();
}

class _ArrivalDialogState extends State<ArrivalDialog> with TickerProviderStateMixin {
  late final ConfettiController _confettiTop;
  late final ConfettiController _confettiBurst;
  late final AnimationController _scaleIn;

  @override
  void initState() {
    super.initState();
    _confettiTop = ConfettiController(duration: const Duration(seconds: 2));
    _confettiBurst = ConfettiController(duration: const Duration(milliseconds: 900));
    _scaleIn = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 260),
      lowerBound: 0.85,
      upperBound: 1.0,
    )..forward();

    // light haptic + confetti
    HapticFeedback.lightImpact();
    _confettiTop.play();
    Future.delayed(const Duration(milliseconds: 300), () => _confettiBurst.play());
  }

  @override
  void dispose() {
    _confettiTop.dispose();
    _confettiBurst.dispose();
    _scaleIn.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final card = Material(
      color: isDark ? const Color(0xFF121417) : Colors.white,
      elevation: 0,
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.fromLTRB(20, 22, 20, 14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: isDark ? Colors.white.withOpacity(0.06) : Colors.black.withOpacity(0.06),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(isDark ? 0.35 : 0.12),
              blurRadius: 24,
              offset: const Offset(0, 18),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Success badge
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: (isDark ? Colors.greenAccent : Colors.green).withOpacity(0.12),
              ),
              child: Icon(Icons.check_rounded, size: 42, color: isDark ? Colors.greenAccent : Colors.green.shade600),
            ),
            const SizedBox(height: 14),
            Text(
              "You’ve arrived!",
              textAlign: TextAlign.center,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              widget.destinationName,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.primary,
              ),
            ),
            if (widget.subtitle != null) ...[
              const SizedBox(height: 8),
              Text(
                widget.subtitle!,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.textTheme.bodyMedium?.color?.withOpacity(0.8),
                ),
              ),
            ],
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      HapticFeedback.selectionClick();
                      Navigator.of(context).maybePop();
                      widget.onSecondary?.call();
                    },
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: theme.colorScheme.outline.withOpacity(0.4)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(widget.secondaryText),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      HapticFeedback.selectionClick();
                      Navigator.of(context).maybePop();
                      widget.onPrimary?.call();
                    },
                    style: ElevatedButton.styleFrom(
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(widget.primaryText),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );

    // Two confetti layers: a top “rain” + a focused burst from center
    return Center(
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Top rain
          Positioned(
            top: MediaQuery.of(context).size.height * 0.15,
            child: ConfettiWidget(
              confettiController: _confettiTop,
              blastDirection: pi / 2, // downwards
              emissionFrequency: 0.08,
              numberOfParticles: 10,
              maxBlastForce: 18,
              minBlastForce: 6,
              gravity: 0.22,
              shouldLoop: false,
              colors: const [
                Color(0xFF7C4DFF),
                Color(0xFF00E5FF),
                Color(0xFFFF4081),
                Color(0xFFFFD740),
                Color(0xFF69F0AE),
              ],
            ),
          ),
          // Center burst
          ConfettiWidget(
            confettiController: _confettiBurst,
            blastDirectionality: BlastDirectionality.explosive,
            emissionFrequency: 0.0,
            numberOfParticles: 32,
            maxBlastForce: 26,
            minBlastForce: 12,
            gravity: 0.25,
            colors: const [
              Color(0xFF7C4DFF),
              Color(0xFF00E5FF),
              Color(0xFFFF4081),
              Color(0xFFFFD740),
              Color(0xFF69F0AE),
            ],
            createParticlePath: _starPath,
          ),
          // Dialog scale-in
          ScaleTransition(scale: _scaleIn, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 20), child: card)),
        ],
      ),
    );
  }

  /// fun star-shaped particles for the center burst
  Path _starPath(Size size) {
    // Draw a 5-point star
    const int points = 5;
    final double outerRadius = size.width / 2;
    final double innerRadius = outerRadius / 2.5;
    final double angle = pi / points;

    final path = Path()..moveTo(size.width / 2, 0);
    for (int i = 0; i < points * 2; i++) {
      final r = i.isEven ? outerRadius : innerRadius;
      final a = i * angle - pi / 2;
      path.lineTo(size.width / 2 + r * cos(a), size.height / 2 + r * sin(a));
    }
    path.close();
    return path;
  }
}
