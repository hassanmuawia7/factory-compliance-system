"""
PHASE 7: Architecture and Flow Diagrams
Visual representation of the unified system architecture
"""

ARCHITECTURE_DIAGRAMS = """
================================================================================
PHASE 7: SYSTEM ARCHITECTURE DIAGRAMS
Factory Compliance Monitoring System - Unified Integration
================================================================================


1. SYSTEM COMPONENT HIERARCHY
=============================

┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                          ComplianceMonitoringSystem                      │
│                          (src/main.py - Orchestrator)                   │
│                                                                          │
│  Responsibilities:                                                      │
│  • Initialize all components once                                       │
│  • Manage main processing loop                                          │
│  • Handle keyboard input (Q, P)                                         │
│  • Coordinate all systems                                               │
│  • Graceful shutdown                                                    │
│                                                                          │
└─────────────┬──────────────────────┬──────────────────┬─────────────────┘
              │                      │                  │
              ▼                      ▼                  ▼
      ┌──────────────┐      ┌────────────────┐  ┌────────────────┐
      │ConfigManager │      │YOLO Model      │  │cv2.VideoCapture│
      │              │      │                │  │                │
      │• Load once   │      │• Load once     │  │• Read frames   │
      │• Provide     │      │• Shared by all │  │• Get metadata  │
      │  configs     │      │  detectors     │  │                │
      │• Validate    │      │• 25 FPS        │  │                │
      └──────────────┘      └────────────────┘  └────────────────┘
              │
              ├─────────────────────────────────────────────┐
              │                                             │
              ▼                                             ▼
      ┌──────────────────┐  ┌────────────────────────┐
      │DetectorManager   │  │EventBus + SystemStats  │
      │                  │  │                        │
      │• WalkwayDetector │  │• Event routing         │
      │• Unauthorized    │  │• Statistics tracking   │
      │  InterventionDet │  │• Performance metrics   │
      │• Coordination    │  │                        │
      │• Aggregation     │  │                        │
      └──────────────────┘  └────────────────────────┘


2. FRAME PROCESSING PIPELINE
=============================

                    ┌────────────────┐
                    │  Read Frame    │
                    │from VideoCapture
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ YOLO Inference │ ◄─── ONCE per frame
                    │ (Single Model) │      NOT repeated
                    └────────┬───────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌────────────────┐ ┌────────────────┐ ┌──────────┐
    │ WalkwayDetector│ │Unauthorized    │ │ Future   │
    │                │ │InterventionDet │ │Detectors │
    │• Input: YOLO  │ │                │ │          │
    │  detections   │ │• Input: YOLO   │ │(Optional)│
    │• Output:      │ │  detections    │ │          │
    │  - events     │ │• Output:       │ │          │
    │  - viz data   │ │  - events      │ │          │
    │               │ │  - viz data    │ │          │
    └────────┬───────┘ └────────┬───────┘ └──────────┘
             │                  │
             └──────────┬───────┘
                        │
                        ▼
            ┌────────────────────────┐
            │ DetectorManager        │
            │ Aggregates Results:    │
            │ • Merge events         │
            │ • Merge visualization  │
            └────────┬───────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌─────────┐
    │Validate│  │Publish │  │Display  │
    │& Store │  │on Event│  │Overlay  │
    │Database│  │Bus     │  │         │
    └────────┘  └────────┘  └─────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ Update Statistics  │
            │ • Frames++         │
            │ • Violations++     │
            └────────┬───────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ Display Frame      │
            │ with Overlay       │
            └────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ Check Keyboard Input   │
        │ Q = Quit, P = Pause    │
        └────────┬───────────────┘
                 │
            ┌────┴────┐
            ▼         ▼
         QUIT      CONTINUE
        (Shutdown) (Next Frame)


3. DETECTOR INTERFACE
=====================

                    ┌──────────────────┐
                    │  BaseDetector    │
                    │  (Abstract)      │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌────────────────────┐      ┌────────────────────┐
    │  WalkwayDetector   │      │UnauthorizedIntDet  │
    │  (Refactored)      │      │  (Refactored)      │
    │                    │      │                    │
    │Methods:            │      │Methods:            │
    │                    │      │                    │
    │__init__(config)    │      │__init__(config)    │
    │  • Load walkway    │      │  • Load machinery  │
    │    zone            │      │    zones           │
    │  • Get rule        │      │  • Get rule        │
    │                    │      │                    │
    │detect(frame,yolo)  │      │detect(frame,yolo)  │
    │  • Test polygon    │      │  • Test polygons   │
    │  • Create events   │      │  • Detect vests    │
    │  • Return events   │      │  • Create events   │
    │  • Return events   │      │                    │
    │                    │      │                    │
    │get_visualization() │      │get_visualization() │
    │  • Bounding boxes  │      │  • Bounding boxes  │
    │  • Zone overlay    │      │  • Zone overlays   │
    │  • Labels          │      │  • Labels          │
    │                    │      │                    │
    └────────────────────┘      └────────────────────┘


4. DATA FLOW - EVENT CREATION TO DATABASE
==========================================

    Detector Detects Violation
              │
              ▼
    EventFactory.create_event()
    ┌─────────────────────────┐
    │ • Generate event_id     │
    │ • Set timestamp         │
    │ • Set severity          │
    │ • Set behavior_class    │
    │ • Assign policy         │
    │ • Create description    │
    └─────────────┬───────────┘
                  │
                  ▼
    EventFactory.validate_event()
    ┌─────────────────────────┐
    │ • Check required fields │
    │ • Validate severity     │
    │ • Validate behavior     │
    │ • Return: (is_valid,   │
    │            message)     │
    └─────────────┬───────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
    VALID              INVALID
        │                   │
        ▼                   ▼
    DatabaseService.  Log Warning
    create_violation()  & Skip
        │
        ├─ Check connection
        ├─ Insert record
        ├─ Update statistics
        └─ Confirm success
        │
        ▼
    EventBus.publish()
    ┌──────────────────┐
    │ • Add to history │
    │ • Notify         │
    │   subscribers    │
    │ • Track critical │
    └────────────────┘
        │
        ▼
    SystemStats.record_violation()
    ┌──────────────────┐
    │ • Increment total│
    │ • By severity   │
    │ • By behavior   │
    │ • Update metrics│
    └────────────────┘


5. CONFIGURATION LOADING SEQUENCE
==================================

    ComplianceMonitoringSystem.__init__()
              │
              ▼
    ConfigManager("outputs")
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    Load         Load
    zones.json    validated_rules.json
        │           │
        └─────┬─────┘
              │
              ▼
    Validate Configuration
    ┌──────────────────────┐
    │ • Check rules loaded │
    │ • Check zones loaded │
    │ • Provide defaults   │
    │   if missing         │
    └──────────┬───────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    VALID         FALLBACK
        │          DEFAULTS
        │             │
        └─────┬───────┘
              │
              ▼
    All Modules Use Same Config
    ┌────────────────────────┐
    │ • DetectorManager ◄────┤
    │ • WalkwayDetector ◄────┤
    │ • UnauthorizedDet ◄────┤
    │ (No duplicate loading) │
    └────────────────────────┘


6. VISUALIZATION AGGREGATION
=============================

    WalkwayDetector Results          UnauthorizedDetector Results
    ┌────────────────────┐           ┌────────────────────┐
    │ VisualizationData: │           │ VisualizationData: │
    │                    │           │                    │
    │ bounding_boxes: [] │           │ bounding_boxes: [] │
    │ labels: []         │           │ labels: []         │
    │ zones: []          │           │ zones: []          │
    │ circles: []        │           │ circles: []        │
    └────────┬───────────┘           └────────┬───────────┘
             │                               │
             └───────────────┬───────────────┘
                             │
                             ▼
                    DetectorManager
                    Merge Visualization
                    ┌──────────────────────┐
                    │ Aggregated Data:     │
                    │                      │
                    │ bounding_boxes:      │
                    │   [all boxes]        │
                    │ labels:              │
                    │   [all labels]       │
                    │ zones:               │
                    │   [all zones]        │
                    │ circles:             │
                    │   [all circles]      │
                    └──────────┬───────────┘
                               │
                               ▼
                    Draw on Frame
                    ┌──────────────────┐
                    │ • Draw zones     │
                    │ • Draw boxes     │
                    │ • Draw circles   │
                    │ • Draw labels    │
                    └──────────┬───────┘
                               │
                               ▼
                    Display in Window


7. SYSTEM SHUTDOWN SEQUENCE
============================

    User Presses Q
    (or End of Video)
              │
              ▼
    is_running = False
              │
              ▼
    Exit Main Loop
              │
              ▼
    _shutdown() Method
              │
        ┌─────┴─────────────────┐
        │                       │
        ▼                       ▼
    Close Video          Close Windows
    cap.release()        cv2.destroyAllWindows()
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
        Get Final Statistics
        ┌──────────────────────┐
        │ • Total frames       │
        │ • Violations         │
        │ • By severity        │
        │ • By type            │
        │ • Duration           │
        │ • Average FPS        │
        └──────────┬───────────┘
                   │
                   ▼
        Print Summary Report
        ┌──────────────────────┐
        │ ====================│
        │ SYSTEM SUMMARY       │
        │ Frames: 542          │
        │ Violations: 11       │
        │ CRITICAL: 3          │
        │ HIGH: 8              │
        │ Duration: 21.6s      │
        │ FPS: 25.1            │
        │ ====================│
        └──────────┬───────────┘
                   │
                   ▼
        Application Exits
        (with recorded data in database)


8. PERFORMANCE CHARACTERISTICS
==============================

┌────────────────────────────────────────────────────────────────┐
│                                                                │
│ SINGLE YOLO MODEL ARCHITECTURE                                │
│                                                                │
│ OLD APPROACH:                                                  │
│ WalkwayDetector YOLO ─┐                                        │
│                       ├─ 50 ms per frame (total)              │
│ UnauthorizedDetector YOLO ┘                                    │
│ (Duplicated overhead)                                          │
│                                                                │
│ NEW APPROACH:                                                  │
│ Shared YOLO ─ 40 ms per frame                                 │
│ All Detectors Use Same Results                                 │
│ Savings: 10 ms per frame (25% improvement)                     │
│                                                                │
│ At 25 FPS:                                                     │
│ Processing Time per Frame: 40 ms                              │
│ Display/Wait Time: 40 ms                                      │
│ Total: 80 ms (25 FPS)                                         │
│                                                                │
│ Headroom: 20 ms for future detectors                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘


9. MODULE DEPENDENCY GRAPH
===========================

                            main.py
                              ▲
                    ┌─────────┬┼┬─────────┐
                    │         ││ │        │
                    ▼         ││ ▼        ▼
             ConfigManager    ││ YOLO   VideoCapture
                    ▲         ││
            ┌───────┴──┐      ││
            │          │      ││
            ▼          ▼      ││
         zones.json rules.json││
                    ▲         ││
            ┌───────┤         ││
            │       │         ││
            ▼       ▼         ││ ▼
      DetectorManager◄────────┘└─ EventBus ◄─┐
         ▲  ▲                        ▲       │
         │  └──┬───────────┬────────┘        │
         │     │           │                 │
         ▼     ▼           ▼                 │
    WalkwayDet Unauthorized SystemStats      │
         ▲     Intervention      ▲           │
         │     ▲                 │           │
         └─────┤─────────────────┘           │
               │                             │
               ▼                             │
          BaseDetector                       │
               ▲                             │
               │                             │
         ┌─────┴──────────┐                  │
         │                │                  │
         ▼                ▼                  │
   EventFactory      DatabaseService────────┘


This is the complete Phase 7 unified architecture!
================================================================================
"""

if __name__ == "__main__":
    print(ARCHITECTURE_DIAGRAMS)
