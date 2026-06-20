# Factory Compliance Monitoring System

AI-powered industrial safety platform for workplace compliance monitoring. The system parses facility policy documents, detects violations in video feeds using YOLOv8 computer vision, classifies severity, routes escalation actions, persists events to SQLite, and exposes results through a Streamlit dashboard and exportable reports.

**Version:** 2.0.0  
**Status:** Submission-ready

---

## 1. Project Overview

The Factory Compliance Monitoring System automates monitoring of unsafe behaviors on a factory production floor. It was built as an AI internship take-home assignment demonstrating end-to-end system design: from policy document ingestion through real-time video analysis to audit logging and operational dashboards.

The system currently implements **three of four** policy domains defined in the facility compliance manual:

| Policy Domain | Status | Detector |
|---|---|---|
| Pedestrian Movement | Implemented | Walkway Violation |
| Equipment Intervention | Implemented | Unauthorized Intervention |
| Forklift Load Management | Implemented | Forklift Overload |
| Electrical Panel Management | Not implemented | — |

Core technologies: **Python**, **YOLOv8 (Ultralytics)**, **OpenCV**, **SQLAlchemy**, **SQLite**, **Streamlit**, **Plotly**, **PyMuPDF**, **OpenAI API** (rule extraction).

---

## 2. Assignment Objective

Build an automated compliance monitoring pipeline that:

1. Extracts enforceable safety rules from a provided policy PDF.
2. Detects unsafe behaviors in factory video footage.
3. Assigns severity levels and escalation actions to each violation.
4. Stores structured compliance events in a database.
5. Presents violations through a monitoring dashboard and exportable reports.

Each violation event must include: `event_id`, `timestamp`, `clip_id`, `zone`, `behavior_class`, `policy_rule_ref`, `event_description`, `severity`, and `escalation_action`.

---

## 3. System Architecture

```
Policy PDF (data/policy/)
        │
        ▼
  PDF Parser ──► policy_text.txt
        │
        ▼
  Rule Extractor (OpenAI) ──► rules.json
        │
        ▼
  Rule Validator ──► validated_rules.json
        │
        ▼
  ConfigManager (zones.json + validated_rules.json)
        │
        ▼
  Main Pipeline (src/main.py)
        │
        ├── YOLOv8 Inference (person + truck classes)
        │
        ├── DetectorManager
        │     ├── WalkwayDetector
        │     ├── UnauthorizedInterventionDetector
        │     └── ForkliftOverloadDetector
        │
        ├── EventFactory (severity + policy mapping)
        │
        ├── EventBus (CRITICAL / VIOLATION events)
        │
        └── DatabaseService ──► SQLite (outputs/compliance_logs.db)
                │
                ├── Streamlit Dashboard
                └── Report Generator (CSV / JSON / Summary)
```

**Design principles:** single YOLO instance per pipeline run, shared configuration via `ConfigManager`, detectors inherit from `BaseDetector` and return events without writing to the database directly, and the main orchestrator handles persistence and console alerting.

---

## 4. Policy Parsing Pipeline

The policy parsing pipeline converts the facility PDF into structured, validated rules consumed by all detectors.

| Step | Script | Input | Output |
|---|---|---|---|
| 1. PDF extraction | `python src/parser/pdf_parser.py` | `data/policy/Compliance_Policy_Manual.pdf` | `outputs/policy_text.txt` |
| 2. Rule extraction | `python src/parser/rule_extractor.py` | `outputs/policy_text.txt` | `outputs/rules.json` |
| 3. Rule validation | `python src/parser/validator.py` | `outputs/rules.json` | `outputs/validated_rules.json` |

**Rule extraction** uses the OpenAI API (`gpt-4o-mini`) with JSON response format to extract four unsafe behaviors. Each rule contains:

- `observable_indicator` — what the detection system should look for
- `policy_reference` — section reference (e.g. `6.3.2`)
- `severity_hint` — expected severity level
- `threshold` — numeric threshold where applicable (e.g. forklift block count)

**Validation** checks required fields and severity values before saving `validated_rules.json`. Detectors read rules at startup through `ConfigManager`.

---

## 5. Detection Modules

All detectors inherit from `BaseDetector`, receive YOLO detections as input (no per-detector model loading), and return standardized event dictionaries.

### Walkway Violation Detection

**File:** `src/detection/walkway_detector_refactored.py`  
**Behavior class:** `walkway_violation`  
**Severity:** HIGH  
**Policy reference:** Section 3.3.2 (from validated rules)

Detects persons (YOLO class 0) whose foot position falls outside the polygon defined in `outputs/zones.json` (`walkway_zone`). Uses a 5-second cooldown to prevent duplicate events for the same ongoing violation.

### Unauthorized Intervention Detection

**File:** `src/detection/unauthorized_intervention_detector_refactored.py`  
**Behavior class:** `unauthorized_intervention`  
**Severity:** CRITICAL  
**Policy reference:** Section 4.3.2 (from validated rules)

Detects persons inside machinery zones (from `zones.json` → `machinery_zones`) who are not wearing a green safety vest. Vest detection uses HSV color analysis on an upper-torso ROI within the person bounding box.

### Forklift Load Management Detection

**File:** `src/detection/forklift_detector_refactored.py`  
**Behavior class:** `forklift_overload`  
**Severity:** CRITICAL  
**Policy reference:** Section 6.3.2 (from validated rules)

Detects forklifts using YOLO class 7 (`truck`) with confidence and area filters. A motion-history check suppresses false positives on stationary machinery.

**Load estimation** uses vertical band counting on orange load pixels within the fork ROI:

1. Crop the upper portion of the truck bounding box.
2. Apply HSV masking for facility load color.
3. Compute row projection and count distinct vertical bands (stack layers).
4. Stabilize the count using a rolling median over recent frames.

**Overload decision:** when the stabilized load count meets or exceeds the policy threshold (default: **3 blocks**, read from `validated_rules.json`) for 3 consecutive frames, a violation event is generated.

**Note:** Forklift footage is present in `data/videos/7_tr3.mp4`. The visible load in provided footage appears compliant (estimated 1–2 units). Overload events are therefore not expected during normal demo runs on that clip.

---

## 6. Severity Classification

Severity is assigned centrally in `src/severity/event_factory.py` via `BEHAVIOR_SEVERITY_MAP`:

| Behavior Class | Severity |
|---|---|
| `walkway_violation` | HIGH |
| `unauthorized_intervention` | CRITICAL |
| `forklift_overload` | CRITICAL |

Policy references are mapped in `BEHAVIOR_POLICY_MAP`. Detectors may override the policy reference with the parsed value from `validated_rules.json` (e.g. forklift uses `6.3.2`).

Compliance score impact (dashboard): `100 − (Critical×5 + High×2 + Medium×0.5)`.

---

## 7. Escalation Pipeline

Escalation actions are derived automatically from severity in `EventFactory._derive_escalation_action()`:

| Severity | Escalation Action |
|---|---|
| CRITICAL, HIGH | Real-time alert triggered + DB log |
| MEDIUM, LOW | Logged to DB only |

When a violation is persisted:

1. `EventFactory.validate_event()` checks all required fields.
2. `DatabaseService.create_violation()` writes to SQLite.
3. `EventBus` publishes the event (`CRITICAL_VIOLATION` for CRITICAL severity).
4. Console output logs the event ID and severity.

---

## 8. Database Schema

**Engine:** SQLite  
**File:** `outputs/compliance_logs.db`  
**ORM model:** `ViolationRecord` in `src/database/models.py`  
**Table:** `violations`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment row ID |
| `event_id` | VARCHAR (unique) | Event identifier (e.g. `EVT-20260620194524…`) |
| `timestamp` | VARCHAR | ISO 8601 timestamp |
| `clip_id` | VARCHAR | Source video filename |
| `zone` | VARCHAR | Detection zone (e.g. Walkway, Machine-Zone, Forklift-Zone) |
| `behavior_class` | VARCHAR | Violation type |
| `policy_rule_ref` | VARCHAR | Policy section reference |
| `event_description` | VARCHAR | Human-readable description |
| `severity` | VARCHAR | CRITICAL / HIGH / MEDIUM / LOW |
| `escalation_action` | VARCHAR | Action taken |

Initialize the database:

```powershell
python src/database/db_manager.py
```

---

## 9. Dashboard Features

**Launch:** `streamlit run src/dashboard/app.py` → http://localhost:8501

The dashboard reads violation records from SQLite via `DatabaseService` and renders:

### Live Feed Monitor

Displays `outputs/latest_frame.jpg`, written by the main pipeline during video processing. Shows pipeline status (LIVE / STALE / OFFLINE) based on frame age.

### Alert Timeline Stream

Chronological stream of recent violations with severity color coding, timestamps, behavior class, and zone.

### Historical Log

**Violation Audit Log** — sortable table of all recorded events with timestamp, event ID, clip ID, zone, severity, behavior class, description, policy reference, and escalation action. Supports filtering by severity, behavior type, and date range, plus event search.

### Additional Sections

- **KPI Cards** — total violations, severity breakdown, compliance score
- **Alert Center** — latest critical/high violations
- **Analytics Dashboard** — severity donut chart, behavior bar chart, time-series trend
- **System Health** — database and pipeline status indicators
- **Export & Reporting** — download CSV/JSON and generate summary reports from the UI

---

## 10. Reports

**Generate reports:**

```powershell
python src/reports/report_generator.py
```

This produces timestamped files in `outputs/reports/`:

| Format | Description |
|---|---|
| CSV | Full violation audit log; `compliance_report_YYYYMMDD_HHMMSS.csv` |
| JSON | Structured event export; `compliance_report_YYYYMMDD_HHMMSS.json` |
| Summary | Text compliance summary; `compliance_summary_YYYYMMDD_HHMMSS.txt` |
| Filtered export | JSON export filtered by severity (CRITICAL/HIGH) |

Reports are generated from the SQLite database and reflect all persisted violation events.

---

## 11. Installation

### Prerequisites

- Python 3.8+ (tested with Python 3.13)
- Windows / Linux / macOS
- 8 GB+ RAM recommended (YOLO inference)
- OpenAI API key (for rule extraction only; pre-generated rules are included in `outputs/`)

### Clone and install dependencies

```powershell
git clone <repository-url>
cd factory-compliance-system
python -m venv venv_fact
.\venv_fact\Scripts\Activate.ps1
pip install -r requirements.txt
```

YOLOv8 Nano weights (`yolov8n.pt`) are downloaded automatically on first run.

---

## 12. Setup

1. **Activate the virtual environment** (required for every session):

   ```powershell
   .\venv_fact\Scripts\Activate.ps1
   python -c "import sys; print(sys.executable)"
   ```

   Verify the path points to `venv_fact`.

2. **Initialize the database:**

   ```powershell
   python src/database/db_manager.py
   ```

3. **Verify configuration files exist in `outputs/`:**

   - `zones.json` — calibrated walkway and machinery zones
   - `validated_rules.json` — validated policy rules

4. **(Optional) Re-run policy parsing** if the policy PDF changes:

   ```powershell
   python src/parser/pdf_parser.py
   python src/parser/rule_extractor.py
   python src/parser/validator.py
   ```

   Rule extraction requires `OPENAI_API_KEY` in a `.env` file.

5. **(Optional) Recalibrate zones** using a reference frame:

   ```powershell
   python src/calibration/zone_selector.py
   ```

---

## 13. Run Commands

### Main detection pipeline

```powershell
python src/main.py
```

Default video: `data/videos/test.mp4`. Specify a clip:

```powershell
python src/main.py data/videos/7_tr3.mp4
```

Press **Q** to quit, **P** to pause. Violations are logged to the database and the latest annotated frame is saved to `outputs/latest_frame.jpg`.

### Dashboard

```powershell
streamlit run src/dashboard/app.py
```

### Reports

```powershell
python src/reports/report_generator.py
```

### Zone calibration

```powershell
python src/calibration/zone_selector.py
```

Interactive tool for defining walkway and machinery zone polygons. Saves to `outputs/zones.json`.

### Forklift overload path testing (validation only)

The overload decision logic can be tested without modifying video files:

```powershell
# Unit tests for overload decision logic
python src/detection/forklift_detector_refactored.py

# End-to-end overload simulation (disabled by default in normal runs)
$env:FORKLIFT_SIMULATE_LOAD = "3"
python src/main.py data/videos/7_tr3.mp4
```

`FORKLIFT_SIMULATE_LOAD` is **disabled by default** and only activates when explicitly set. Do not use during normal demos.

---

## 14. Project Structure

```
factory-compliance-system/
├── data/
│   ├── policy/
│   │   └── Compliance_Policy_Manual.pdf
│   └── videos/
│       ├── test.mp4              # Default demo clip
│       ├── 7_tr3.mp4             # Forklift activity clip
│       └── ...                   # Additional test footage
├── outputs/
│   ├── compliance_logs.db        # SQLite event database
│   ├── zones.json              # Calibrated detection zones
│   ├── validated_rules.json    # Validated policy rules
│   ├── policy_text.txt         # Extracted policy text
│   ├── rules.json              # Raw extracted rules
│   ├── latest_frame.jpg        # Latest pipeline frame (dashboard feed)
│   └── reports/                  # Generated report exports
├── src/
│   ├── main.py                   # Main pipeline entry point
│   ├── calibration/
│   │   └── zone_selector.py      # Zone calibration tool
│   ├── core/
│   │   ├── config_manager.py     # Configuration loader
│   │   ├── detector_manager.py   # Detector coordination
│   │   ├── event_bus.py          # Event pub/sub
│   │   └── system_stats.py       # Runtime statistics
│   ├── dashboard/
│   │   └── app.py                # Streamlit dashboard
│   ├── database/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── db_manager.py         # Database initialization
│   │   └── database_service.py   # CRUD service layer
│   ├── detection/
│   │   ├── base_detector.py
│   │   ├── walkway_detector_refactored.py
│   │   ├── unauthorized_intervention_detector_refactored.py
│   │   └── forklift_detector_refactored.py
│   ├── parser/
│   │   ├── pdf_parser.py
│   │   ├── rule_extractor.py
│   │   └── validator.py
│   ├── reports/
│   │   └── report_generator.py
│   └── severity/
│       └── event_factory.py      # Event creation + severity mapping
├── requirements.txt
└── README.md
```

---

## 15. Known Limitations

**Electrical Panel Management is intentionally not implemented.** The policy manual defines this domain (Section 5), but no electrical panel footage or calibrated zones are available in the provided dataset. The rule is extracted and validated in `validated_rules.json` (`opened_panel_cover`) but has no active detector.

**Forklift overload logic is fully implemented** but the provided footage (`7_tr3.mp4`) shows a compliant load (estimated 1–2 stack units). Overload violation events are therefore not expected during normal demo runs. Use `FORKLIFT_SIMULATE_LOAD=3` to validate the overload event path end-to-end.

**Forklift detection uses YOLO COCO class `truck`** as a forklift proxy. This works on moving forklifts but can produce false positives on large stationary machinery if motion filtering is insufficient. Motion-history filtering is applied to reduce this.

**Load estimation is heuristic-based** (HSV color masking + vertical band counting). It does not use custom-trained models and may not generalize to all load types or lighting conditions.

**Rule extraction requires an OpenAI API key.** Pre-generated `validated_rules.json` is included so the detection pipeline runs without re-extraction.

**Single-camera processing.** The main pipeline processes one video source at a time.

---

## 16. Future Improvements

Realistic extensions that build on the current architecture:

- **Electrical Panel Monitoring** — detector for open panel covers using zone-based visual inspection, once suitable footage and calibration data are available.
- **Email Alerts** — outbound notifications on CRITICAL/HIGH events via SMTP or webhook, triggered from the existing `EventBus`.
- **Multi-Camera Support** — parallel or round-robin processing of multiple RTSP/file sources through the existing `DetectorManager`.
- **Improved Forklift Load Estimation** — fine-tuned object detection or depth-aware counting to replace the current HSV band-counting heuristic.

---

**Last Updated:** June 2026  
**Version:** 2.0.0
