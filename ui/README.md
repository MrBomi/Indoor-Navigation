# INDIGO – Indoor Navigation System (UI)

INDIGO is a mobile application for **indoor navigation** built with **Flutter (Dart)**.  
It provides real-time indoor positioning using Wi-Fi fingerprints, magnetic field data, and PDR (Pedestrian Dead Reckoning).  
This repository contains the **UI module**, which communicates with the backend and provides building maps, live user location, and navigation paths.

---

## 🚀 Features

- **Building & Floor Management**
  - Upload floor plans (DWG/PDF) → converted to SVG.
  - Interactive map viewer with zoom, pan, and room labeling.

- **Indoor Positioning**
  - Wi-Fi fingerprinting for user location.
  - Magnetic + sensor fusion (accelerometer, compass) for improved accuracy.
  - Step detection (PDR) with north alignment calibration.

- **Navigation**
  - A* pathfinding on the visibility graph.
  - Live navigation mode: shows predicted position with blue dot.
  - Retry option for location recalibration.

- **Admin Tools**
  - Fingerprint collection via CSV export.
  - Wi-Fi training data upload to backend.
  - Room and door classification.

---

## 🏗️ Project Structure

- `lib/`
  - `models/` → Core data models (Building, FloorData, UserLocation, etc.)
  - `services/` → API services (Wi-Fi positioning, PDR, data collection).
  - `widgets/` → Reusable UI components (floor picker, dialogs, navigation bottom sheet).
  - `utils/` → SVG parsing, scale conversions.

---

## 📱 Getting Started

### Prerequisites
- Flutter (>=3.0)
- Android Studio / VS Code
- Backend server ([INDIGO Server](https://github.com/MrBomi/Indoor-Navigation))

### Installation
```bash
git clone https://github.com/NoamKont/INDIGO_ui.git
cd INDIGO_ui
flutter pub get
