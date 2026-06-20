# PHASE 7: System Integration and Main Pipeline
## Implementation Plan

### Current State Analysis

#### ✅ WORKING MODULES (DO NOT BREAK)
1. **Event Factory** (`src/severity/event_factory.py`)
   - Creates standardized events
   - BehaviorClass enum (WALKWAY_VIOLATION, UNAUTHORIZED_INTERVENTION)
   - SeverityLevel enum (CRITICAL, HIGH, MEDIUM, LOW)
   - Event validation logic

2. **Database Service** (`src/database/database_service.py`)
   - CRUD operations
   - Compliance score calculations
   - Statistics queries

3. **Report Generator** (`src/reports/report_generator.py`)
   - CSV, JSON, Summary exports
   - Compliance recommendations

4. **Dashboard** (`src/dashboard/app.py`)
   - Real-time visualization
   - Reads from database

#### ❌ ISSUES IN CURRENT DETECTORS
1. **Duplicate YOLO Initialization**
   - walkway_detector.py loads YOLO
   - unauthorized_intervention_detector.py loads YOLO
   - Each runs separately → inefficient

2. **Direct JSON File Loading**
   - Each detector loads zones.json directly
   - No centralized configuration
   - Hard to maintain/test

3. **Tight Coupling**
   - Detectors handle database writes
   - Detectors handle report generation (unauthorized detector)
   - Detectors create their own OpenCV windows
   - Mixed concerns

4. **No Event Pipeline**
   - Events created inside detectors
   - Database writes scattered
   - No unified event flow

5. **No Performance Optimization**
   - Frame processing not shared
   - Duplicate polygon tests
   - No frame skipping option

### Target Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Entry Point)                │
│                                                         │
│  1. Load Configuration (ConfigManager)                 │
│  2. Initialize YOLO (Once)                             │
│  3. Initialize Database (Once)                         │
│  4. Open Video (Once)                                  │
│  5. Run Main Loop:                                     │
│     ├─ Read Frame                                      │
│     ├─ YOLO Inference (Once per frame)                │
│     ├─ Run All Detectors on Same Frame                │
│     ├─ Collect Events                                 │
│     ├─ Route via EventBus                             │
│     ├─ Save to Database                               │
│     ├─ Update Statistics                              │
│     ├─ Display Unified Overlay                        │
│     └─ Continue or Exit                               │
└─────────────────────────────────────────────────────────┘
```

### Core Components to Create

#### 1. **ConfigManager** (`src/core/config_manager.py`)
```
Responsibilities:
- Load validated_rules.json once
- Load zones.json once
- Provide get_rule(rule_name)
- Provide get_walkway_zone()
- Provide get_machinery_zones()
- Handle missing files gracefully
- No detector should load JSON files
```

#### 2. **EventBus** (`src/core/event_bus.py`)
```
Responsibilities:
- Register event listeners
- Publish events to subscribers
- Route CRITICAL events separately
- Event filtering capabilities
Future-proof for new detectors
```

#### 3. **DetectorManager** (`src/core/detector_manager.py`)
```
Responsibilities:
- Initialize all detectors
- Provide process_frame(frame, yolo_detections)
- Return all events from all detectors
- Manage detector configuration
- Handle detector failures gracefully
```

#### 4. **SystemStats** (`src/core/system_stats.py`)
```
Responsibilities:
- Track frames processed
- Track violations by severity
- Track violations by behavior
- Provide summary statistics
- Expose get_summary()
```

#### 5. **Refactored Detectors**
```
WalkwayDetector Class:
- __init__(config_manager)
- detect(frame, yolo_detections) → list[Event]
- get_visualization_data() → dict{boxes, labels, zones}

UnauthorizedInterventionDetector Class:
- __init__(config_manager)
- detect(frame, yolo_detections) → list[Event]
- get_visualization_data() → dict{boxes, labels, zones}
```

### Implementation Order

1. **ConfigManager** - Foundation for all other modules
2. **EventBus** - Centralized event routing
3. **SystemStats** - Statistics tracking
4. **WalkwayDetector (Class)** - Refactored detector
5. **UnauthorizedInterventionDetector (Class)** - Refactored detector
6. **DetectorManager** - Coordinator
7. **main.py** - Entry point with unified loop
8. **Overlay System** - Unified visualization
9. **Graceful Shutdown** - Cleanup and summary

### Code Quality Principles

✅ **DRY (Don't Repeat Yourself)**
- Single YOLO inference
- Shared detections across detectors
- No duplicate configuration loading

✅ **SOLID Principles**
- Single Responsibility: Each class has one job
- Open/Closed: Easy to add new detectors
- Dependency Inversion: Detectors depend on ConfigManager (abstraction)

✅ **Testability**
- Detectors can be tested with mock frames
- ConfigManager can be mocked
- EventBus can be tested independently

✅ **Performance**
- One YOLO model for entire system
- Detections shared across all detectors
- Optional frame skipping
- No unnecessary copies

### Files to Create

```
src/core/
├── __init__.py (NEW)
├── config_manager.py (NEW)
├── event_bus.py (NEW)
├── detector_manager.py (NEW)
└── system_stats.py (NEW)

src/detection/
├── walkway_detector.py (REFACTORED → CLASS)
├── unauthorized_intervention_detector.py (REFACTORED → CLASS)
└── base_detector.py (NEW - Abstract base class)

src/
└── main.py (NEW - Entry point)
```

### Files to Keep Unchanged

✅ src/database/database_service.py
✅ src/severity/event_factory.py
✅ src/reports/report_generator.py
✅ src/dashboard/app.py
✅ outputs/zones.json
✅ outputs/validated_rules.json

### Success Criteria

✅ Run: `python src/main.py`
✅ System loads configs once
✅ YOLO loaded once
✅ Both detectors run on same frame
✅ Events collected and saved centrally
✅ Statistics tracked in real-time
✅ Single OpenCV window displays unified overlay
✅ Press Q to exit with summary
✅ Database populated correctly
✅ Dashboard reads from database
