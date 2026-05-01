# Project High-Level Architecture Graph (Interview Version)

## 1) One-Screen High-Level Graph

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        U1["Flutter Mobile App (ui/)"]
        U2["Admin Flows: Building/Floor setup, calibration, scan upload"]
        U3["User Flows: map view, route request, live location"]
    end

    subgraph API["Application/API Layer"]
        A1["Flask App Factory (run.py, server/__init__.py)"]
        A2["REST Blueprint Endpoints (server/endPoints.py)"]
        A3["In-Memory Session Services<br/>- mangerBuldings (floor creation state)<br/>- PredictManager (tracking sessions)"]
    end

    subgraph Domain["Core Domain/Computation Layer (core/)"]
        D1["Floor Generation Pipeline<br/>DXF + YAML -> geometry -> graph/grid -> SVG"]
        D2["Routing Engine (A* on indoor graph)"]
        D3["Positioning Engine<br/>WKNN + HMM smoothing"]
        D4["Coordinate Transform Layer<br/>raw <-> svg, cell <-> coordinate"]
    end

    subgraph Data["Data & Storage Layer"]
        DB1["PostgreSQL via SQLAlchemy<br/>buildings, floors, doors, graphs"]
        DB2["Cloudflare R2 (S3 API)<br/>fingerprint CSV scan tables"]
        DB3["Derived floor assets persisted as DB text/json<br/>SVG, graph json, grid mappings"]
    end

    U1 --> A1 --> A2
    U2 --> A2
    U3 --> A2

    A2 --> A3
    A2 --> D1
    A2 --> D2
    A2 --> D3
    A2 --> D4

    D1 --> DB1
    D1 --> DB3
    D2 --> DB1
    D3 --> DB2
    D3 --> DB1
    D4 --> DB1
```

---

## 2) Core Runtime Flows (High-Level, but complete)

### A. Floor Onboarding Flow (Admin)

```mermaid
sequenceDiagram
    participant Admin as Admin App
    participant API as Flask Endpoints
    participant BuildMgr as mangerBuldings
    participant Core as Core Pipeline (App/Geometry/Bitmap/Svg)
    participant DB as PostgreSQL

    Admin->>API: POST /building/add
    Admin->>API: POST /floor/add (dwg + yaml + buildingId + floorId)
    API->>BuildMgr: addBuilding(...)
    BuildMgr->>Core: startProccesCreateNewBuilding()
    Core-->>Admin: initial SVG preview
    Admin->>API: POST /floor/calibrate (two points, real distance, north_offset)
    API->>BuildMgr: continueAddBuilding(...)
    BuildMgr->>Core: createFloor() -> graph/grid/doors/svg
    BuildMgr->>DB: persist Floor + Graph + Doors
    API-->>Admin: doors for naming
```

### B. Navigation Route Flow (User)

```mermaid
sequenceDiagram
    participant User as User App
    participant API as Flask Endpoints
    participant DB as DB Managers
    participant Route as Routing Logic (A*)

    User->>API: GET /floor/route/get or /floor/getRouteList
    API->>DB: load graph + floor bounds + doors
    API->>Route: resolve start/goal and run A*
    Route-->>API: raw path cells/points
    API->>DB: raw->svg conversion
    API-->>User: SVG route overlay or list of path points
```

### C. Real-Time Positioning Flow (User)

```mermaid
sequenceDiagram
    participant User as User App (Wi-Fi scan)
    participant API as Flask Endpoints
    participant R2 as R2 Scan Table Storage
    participant WKNN as WKNN Predictor
    participant HMM as HMM Session Smoother
    participant DB as Graph/Grid Managers

    User->>API: POST /predict/top1 (featureVector)
    API->>R2: download floor fingerprint table
    API->>WKNN: candidate cell estimation
    WKNN-->>API: top prediction
    API->>DB: cell->coord + raw->svg
    API-->>User: initial location

    User->>API: POST /predict/get (featureVector + previous location + sessionId)
    API->>WKNN: top-k candidate cells
    API->>DB: previous svg->raw->cell + grid adjacency
    API->>HMM: transition + emission fusion (viterbi)
    HMM-->>API: best current cell
    API->>DB: cell->coord + raw->svg
    API-->>User: smoothed location + confidence
```

---

## 3) Component Responsibilities

- `ui/`: Flutter app for admin setup and user navigation/location UX.
- `server/endPoints.py`: orchestration layer, API contract, request/response handling.
- `server/DataBaseManger/*`: persistence adapters for floors, graphs, doors, and files.
- `core/`: computational heart (CAD parsing, geometry extraction, graph/grid creation, path operations, SVG ops).
- `core/predict/wknn_service.py`: Wi-Fi fingerprint inference against cached floor scan tables.
- `core/predict/hmm_model.py` + `server/predictManager.py`: short-lived session smoothing for continuous movement.

---

## 4) Data Model Snapshot (High-Level)

- `Building`: metadata (`id`, `name`, `city`, `address`).
- `Floor`: calibrated map artifacts and bounds (`svg_data`, `grid_svg`, `x/y min/max`, `one_cm_svg`, `north_offset`).
- `Door`: indoor landmarks and names (raw + scaled coordinates).
- `Graph`: serialized navigable graph + cell mappings + grid adjacency.
- Fingerprint datasets: CSV files in Cloudflare R2 per `building/floor`.

---

## 5) Deployment/Infra View

```mermaid
flowchart TB
    C["Flutter mobile clients"] --> S["Flask service (single deployable)"]
    S --> P["PostgreSQL"]
    S --> R["Cloudflare R2 (S3 compatible)"]
```

- Current architecture is a modular monolith (cleanly separated by domain packages).
- Easy evolution path: split prediction and floor-processing pipelines into dedicated services later.

---

## 6) Overview

This system is a Flutter client talking to a Flask backend that acts as an orchestration layer.
At a high level, we have three core capabilities: floor onboarding, routing, and live positioning.
For onboarding, CAD files are processed into indoor graphs and SVG assets, then persisted.
For routing, the API pulls graph data and computes shortest indoor paths, returning SVG overlays or route points.
For positioning, we combine Wi-Fi fingerprint matching (WKNN) with session-aware HMM smoothing for stable movement.
PostgreSQL stores building/floor/graph metadata, while Cloudflare R2 stores larger scan-table CSV datasets.

---

## 7) File Map

- Entry point: `run.py`
- App bootstrap: `server/__init__.py`
- API surface: `server/endPoints.py`
- Domain computation: `core/app.py`, `core/GeometryExtractor.py`, `core/ManagerFloor.py`, `core/SvgManager.py`
- Prediction: `core/predict/wknn_service.py`, `core/predict/hmm_model.py`, `server/predictManager.py`
- Persistence: `server/models.py`, `server/DataBaseManger/floorManager.py`, `server/DataBaseManger/graphManger.py`, `server/DataBaseManger/filesManager.py`
