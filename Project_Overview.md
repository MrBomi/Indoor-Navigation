# Project Overview

## Opening (10-15 sec)
- Indoor GPS fails indoors.
- We built indoor positioning + navigation.
- Users get stable live location and route guidance.

## Product Flow
- Add building.
- Add floor (`DWG/DXF + config`).
- Process map and doors.
- North alignment and 2 points for order of magnitude.
- Calibrate and scan floor (Fingerprint csv).
- User picks building and floor.
- User picks destination.
- System navigates in real time.

## Core Tech
- Routing: `A*`
- Positioning: `WKNN`
- Smoothing: `HMM + Viterbi`
- Motion signal: `PDR`

## My Role
- Built WiFi RSSI positioning flow.
- Implemented `WKNN` prediction API.
- Integrated backend prediction pipeline.
- Worked on `HMM` smoothing behavior.

## Main Challenges
- WiFi noise.
- Sensor drift.
- Prediction jitter.
- Fast repeated requests.

## Key Trade-Offs
- `Monolith`:
  - + Fast MVP
  - - Weaker scaling boundaries
- `WKNN` vs `KNN`:
  - + Better weighted predictions
  - - More tuning
- Heavy JSON/SVG in SQL:
  - + Fast implementation
  - - Not ideal at scale

## Bottlenecks
- Frequent prediction calls.
- Frequent graph/mapping reads.

## Improvement Plan
- Cache hot graph/mapping data.
- Measure latency per endpoint.
- Move heavy artifacts to object storage.
- Keep SQL for relational metadata.

## Closing (10 sec)
- MVP worked well.
