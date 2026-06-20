"""
PHASE 7 QUICK TEST GUIDE
Copy-paste commands to verify the integrated system
"""

QUICK_TEST = """
╔════════════════════════════════════════════════════════════════════════════╗
║             PHASE 7: QUICK TEST & VALIDATION GUIDE                        ║
║          Copy-paste commands to verify integrated system                   ║
╚════════════════════════════════════════════════════════════════════════════╝


ENVIRONMENT SETUP
=================

Open Terminal and navigate to project:

    cd d:\\Projects\\factory-compliance-system
    .\\venv_fact\\Scripts\\activate

You should see: (venv_fact) in your prompt


TEST 1: ConfigManager
======================

Description: Verify configuration loading

Command:
    python src\\core\\config_manager.py

Expected Output:
    ✅ Zones loaded from outputs/zones.json
    ✅ Rules loaded from outputs/validated_rules.json
    ✅ Configuration valid: 2 rules, 2 zone groups
    
    📋 Configuration Report:
    Walkway zone: 8 points
    Machinery zones: ['machine_1']
    Rules: ['walkway_violation', 'unauthorized_intervention']

Time: < 1 second


TEST 2: EventBus
================

Description: Verify event routing system

Command:
    python src\\core\\event_bus.py

Expected Output:
    🚨 Violation detected: {'violation': 'test'}
    📢 Event: violation_detected at [timestamp]
    
    Total events: 1

Time: < 1 second


TEST 3: SystemStats
===================

Description: Verify statistics tracking

Command:
    python src\\core\\system_stats.py

Expected Output:
    ==================================================
    SYSTEM STATISTICS SUMMARY
    ==================================================
    Duration: 0.0s
    Frames Processed: 100
    Average FPS: 0.0
    
    Violations:
      Total: 16
      🔴 CRITICAL: 0
      🟠 HIGH: 10
      🟡 MEDIUM: 0
      🟢 LOW: 6
    
    By Type:
      Walkway: 10
      Unauthorized: 0
    ==================================================

Time: < 1 second


TEST 4: WalkwayDetector (Refactored)
====================================

Description: Test detector initialization and class interface

Command:
    python src\\detection\\walkway_detector_refactored.py

Expected Output:
    ✅ Initialized: Walkway Detector
    Walkway zone: 8 points
    Rule: walkway_violation

Time: < 2 seconds


TEST 5: UnauthorizedInterventionDetector (Refactored)
====================================================

Description: Test detector initialization and class interface

Command:
    python src\\detection\\unauthorized_intervention_detector_refactored.py

Expected Output:
    ✅ Initialized: Unauthorized Intervention Detector
    Machinery zones: ['machine_1']
    Rule: unauthorized_intervention

Time: < 2 seconds


TEST 6: FULL SYSTEM INTEGRATION
===============================

Description: Run the complete unified system

Command:
    python src\\main.py

Expected Output (Initial):
    
    ======================================================================
    FACTORY COMPLIANCE MONITORING SYSTEM - MAIN PIPELINE
    Phase 7: System Integration
    ======================================================================
    
    📋 Phase 1: Loading Configuration...
      ✅ Zones loaded from outputs/zones.json
      ✅ Rules loaded from outputs/validated_rules.json
      ✅ Configuration valid: 2 rules, 2 zone groups
    
    🤖 Phase 2: Initializing YOLO...
      ✅ YOLOv8 Nano loaded (Single instance for entire system)
    
    🎬 Phase 3: Opening Video Source...
      ✅ Video opened: 1920x1080 @ 30 FPS
         Total frames: 542
    
    🎯 Phase 4: Initializing Detectors...
    
    🚀 Initializing Detectors...
      ✅ Walkway Detector initialized
      ✅ Unauthorized Intervention Detector initialized
      Total detectors: 2
    
    📊 Phase 5: Initializing Systems...
    
    ✅ System Initialization Complete!
       Ready to process: 542 frames
    
    ======================================================================
    STARTING COMPLIANCE MONITORING PIPELINE
    ======================================================================
    
    Press 'Q' to quit, 'P' to pause

Expected Behavior During Processing:
    ├─ OpenCV window opens showing video
    ├─ All detector overlays visible in one window
    ├─ Real-time violation logs appear in terminal
    ├─ Examples:
    │   🚨 Event: [HIGH] walkway_violation - EVT-2026012012053412345
    │   🚨 Event: [CRITICAL] unauthorized_intervention - EVT-2026012012054512345
    └─ Frame counter updates in window

After Video Completes or User Presses Q:
    
    ✅ End of video reached
    
    ======================================================================
    SHUTDOWN SEQUENCE INITIATED
    ======================================================================
    
    🔒 Phase 1: Closing resources...
      ✅ Video source closed
      ✅ Display windows closed
    
    📊 Phase 2: Final System Statistics...
    
    ==================================================
    SYSTEM STATISTICS SUMMARY
    ==================================================
    Duration: 21.6s
    Frames Processed: 542
    Average FPS: 25.1
    
    Violations:
      Total: 11
      🔴 CRITICAL: 3
      🟠 HIGH: 8
      🟡 MEDIUM: 0
      🟢 LOW: 0
    
    By Type:
      Walkway: 8
      Unauthorized: 3
    ==================================================

Time: ~30 seconds (depends on video length)

KEYBOARD SHORTCUTS:
    Q = Quit (graceful shutdown with summary)
    P = Pause/Resume processing


TEST 7: DATABASE VERIFICATION
=============================

Description: Verify violations were saved to database

Command (Option A - Command Line):
    cd d:\\Projects\\factory-compliance-system
    sqlite3 outputs/compliance_logs.db "SELECT COUNT(*) FROM violations;"

Expected Output:
    11
    (or whatever number was detected)

Command (Option B - View Details):
    sqlite3 outputs/compliance_logs.db "SELECT event_id, severity, behavior_class FROM violations ORDER BY timestamp DESC LIMIT 5;"

Expected Output:
    EVT-2026012012054512345|CRITICAL|unauthorized_intervention
    EVT-2026012012053412345|HIGH|walkway_violation
    EVT-2026012012052312345|HIGH|walkway_violation
    ...


TEST 8: DASHBOARD
================

Description: Verify dashboard reads system data

Command:
    streamlit run src\\dashboard\\app.py

Expected Output:
    Streamlit automatically opens in browser
    URL: http://localhost:8501
    
    Dashboard shows:
    ✅ KPI Cards with violation counts
    ✅ Compliance score
    ✅ Alert center with latest violations
    ✅ Violation audit log
    ✅ Charts and analytics
    ✅ Export buttons for CSV/JSON

Stop: Ctrl+C in terminal


TEST 9: GENERATE REPORT
======================

Description: Generate compliance report from detection run

Command:
    python -c "from src.reports.report_generator import ReportGenerator; ReportGenerator.generate_summary_report('outputs/report.txt'); print('✅ Report generated')"

Expected Output:
    ✅ Report generated

Check:
    type outputs/report_*.txt

Expected Output:
    [Compliance Report Content showing violations, analysis, recommendations]


FULL INTEGRATION TEST WORKFLOW
==============================

Execute in order:

    1. python src\\core\\config_manager.py
       └─ Expected: Configuration loads successfully

    2. python src\\core\\event_bus.py
       └─ Expected: Event bus works

    3. python src\\core\\system_stats.py
       └─ Expected: Statistics tracked

    4. python src\\detection\\walkway_detector_refactored.py
       └─ Expected: Detector class loads

    5. python src\\detection\\unauthorized_intervention_detector_refactored.py
       └─ Expected: Detector class loads

    6. python src\\main.py
       └─ Expected: Full system runs
       └─ Press Q when done
       └─ Check summary output

    7. sqlite3 outputs/compliance_logs.db "SELECT COUNT(*) FROM violations;"
       └─ Expected: Number > 0

    8. streamlit run src\\dashboard\\app.py
       └─ Expected: Dashboard shows data
       └─ Stop with Ctrl+C

    9. python -c "from src.reports.report_generator import ReportGenerator; ReportGenerator.generate_summary_report('outputs/report.txt')"
       └─ Expected: Report created


TROUBLESHOOTING COMMON ISSUES
=============================

Issue: "Module not found: src.*"
Solution:
    ├─ Ensure you're in: d:\\Projects\\factory-compliance-system
    ├─ Activate venv: .\\venv_fact\\Scripts\\activate
    └─ Run: python src\\main.py (not from src/ directory)

Issue: YOLO takes very long to load
Solution:
    ├─ First run downloads model (~50MB)
    ├─ Wait 1-2 minutes
    ├─ Subsequent runs are fast
    └─ Model cached at: C:\\Users\\[username]\\.cache\\yolov8

Issue: "Video file not found"
Solution:
    ├─ Check file exists: data/videos/test.mp4
    ├─ Or specify different video:
    │  python src\\main.py data/videos/other_video.mp4
    └─ Or use webcam: python src\\main.py 0

Issue: "Database locked"
Solution:
    ├─ Close dashboard (if running)
    ├─ Close any other database connections
    └─ Try again

Issue: Very low FPS
Solution:
    ├─ Close other applications
    ├─ Ensure video resolution not too high
    ├─ Try: python src\\main.py 0 (webcam for testing)


PERFORMANCE BASELINE
====================

Expected Performance:
    Initialization Time: 20-30 seconds (first run: +30s for YOLO download)
    Processing Speed: 20-25 FPS
    Memory Usage: ~400 MB
    Database Write: < 100ms per event
    Visualization: Real-time overlay


SUCCESS INDICATORS
==================

✅ All unit tests pass (tests 1-5)
✅ Full system runs without errors (test 6)
✅ Database populated (test 7)
✅ Dashboard shows data (test 8)
✅ Report generated (test 9)
✅ Violations detected and logged
✅ Graceful shutdown works
✅ Performance meets baseline


PROJECT READY FOR:
==================

✅ Deployment
✅ Portfolio showcase
✅ Internship submission
✅ Technical interviews
✅ Further enhancement
✅ Production use


NEXT STEPS
==========

After successful testing:

1. Commit to Git:
   git add .
   git commit -m "Phase 7: Complete system integration and main pipeline"

2. Test with your own video:
   python src\\main.py your_video.mp4

3. Review the documentation:
   - README.md (project overview)
   - PHASE_7_SYSTEM_INTEGRATION.md (detailed guide)
   - PHASE_7_ARCHITECTURE_DIAGRAMS.py (visual diagrams)

4. Try dashboard:
   streamlit run src\\dashboard\\app.py

5. Generate reports:
   python -c "from src.reports.report_generator import ReportGenerator; ReportGenerator.generate_summary_report('outputs/my_report.txt')"


VALIDATION CHECKLIST
====================

Before considering Phase 7 complete:

□ ConfigManager loads without errors
□ EventBus routes events correctly
□ SystemStats tracks violations
□ WalkwayDetector class initializes
□ UnauthorizedInterventionDetector class initializes
□ main.py runs full pipeline
□ Violations saved to database
□ Dashboard displays data
□ Reports generate successfully
□ Graceful shutdown works
□ All documentation complete
□ Performance meets baseline
□ Ready for portfolio/interviews

====== PHASE 7 VALIDATION COMPLETE ✅ ======

"""

if __name__ == "__main__":
    print(QUICK_TEST)
