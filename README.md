# Indoor Navigation

Indoor navigation and positioning system built for environments where GPS is unreliable (inside buildings).

The project combines:
- Indoor map onboarding from CAD files (`DWG/DXF` + YAML config)
- Route planning on indoor graphs (`A*`)
- Real-time user localization from Wi-Fi fingerprints (`WKNN`)
- Temporal smoothing for stable movement (`HMM + Viterbi`)
- Mobile client experience for admin setup and user navigation (Flutter)

---

## Repository Structure

- `server/` - Flask API layer, endpoint orchestration, DB managers
- `core/` - geometry extraction, graph/grid generation, routing, prediction logic
- `ui/` - Flutter mobile app (admin + user flows)
- `res/` - sample resources, configs, generated SVG/graph artifacts
- `interview-prep/` - architecture and technical explanation notes

---

## High-Level Architecture

```mermaid
flowchart LR
    Client["Flutter Mobile App"] --> API["Flask API (server/endPoints.py)"]
    API --> Core["Core Engine (core/)"]
    API --> DB["PostgreSQL (SQLAlchemy models)"]
    API --> R2["Cloudflare R2 (scan_table.csv storage)"]
    Core --> DB
```

### Main Runtime Flows

1. **Floor onboarding (admin)**  
   Upload `dwg + yaml` -> generate floor SVG + indoor graph + doors -> calibrate -> persist.

2. **Route generation (user)**  
   Select building/floor/start/goal -> run `A*` on stored graph -> return route SVG or route points.

3. **Live positioning (user)**  
   Send Wi-Fi feature vector -> `WKNN` candidate estimation -> `HMM` smoothing with session context -> return `svgX/svgY`.

---

## Tech Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- PostgreSQL
- SciPy, NumPy, Pandas
- Shapely, ezdxf, svgwrite
- boto3 (Cloudflare R2 via S3-compatible API)

### Mobile
- Flutter (Dart)

### Core Algorithms
- Routing: `A*`
- Positioning: `WKNN`
- Smoothing: `HMM + Viterbi`
- Auxiliary motion support in client: `PDR`

---

## Data Model (High-Level)

- `Building`: building metadata
- `Floor`: SVG/map artifacts, bounds, calibration values (`one_cm_svg`, `north_offset`)
- `Door`: door/room anchors and names
- `Graph`: serialized indoor graph and cell mappings
- Fingerprint scan tables: stored in R2 (`building_<id>/floor_<id>/scan_table.csv`)

---

## Getting Started

## 1) Clone

```bash
git clone <your-repo-url>
cd Indoor-Navigation-main
```

## 2) Backend Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```env
# Option A: single DB URL
DATABASE_URL=postgresql://user:password@localhost:5432/indoor_navigation

# Option B: fallback parts (used if DATABASE_URL is missing)
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=indoor_navigation

# Cloudflare R2
R2_ACCESS_KEY_ID=your_key
R2_SECRET_ACCESS_KEY=your_secret
R2_ENDPOINT=https://<accountid>.r2.cloudflarestorage.com
R2_BUCKET=your_bucket_name
```

Run the server:

```bash
python run.py
```

By default, the API runs on:
- `http://0.0.0.0:8574`

## 3) Flutter UI Setup

```bash
cd ui
flutter pub get
flutter run
```

> Update API base URL/domain in `ui/lib/constants.dart` to match your backend deployment.

---

## API Overview

Selected endpoints exposed by `server/endPoints.py`:

- `POST /building/add` - create building
- `GET /building/get` - list buildings
- `GET /building/getFloors` - list floors in building
- `POST /floor/add` - upload floor (`dwg + yaml`)
- `POST /floor/calibrate` - complete floor calibration
- `GET /floor/getSvgDirect` - fetch floor SVG
- `GET /floor/route/get` - route overlay SVG
- `GET /floor/getRouteList` - route coordinates list
- `POST /floor/scan/upload` - upload fingerprint CSV
- `POST /predict/top1` - single-step location prediction
- `POST /predict/get` - session-smoothed prediction

---

## Development Notes

- Current architecture is a **modular monolith** for fast iteration.
- Heavy artifacts are mixed between DB text fields and object storage.
- For scale, likely next steps:
  - cache hot graph/mapping reads
  - split prediction/floor processing into dedicated services
  - move more heavy artifacts to object storage

---

## Related Docs

- `Project_Overview.md`
- `High Level Architecture.md`
- `interview-prep/07_high_level_architecture_graph.md`

