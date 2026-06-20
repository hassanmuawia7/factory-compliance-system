"""
PROJECT_VALIDATION.py
Factory Compliance System - Project Validation Script
Verifies all necessary files and configurations exist.
"""

import os
import sys
import json
from pathlib import Path


class ProjectValidator:
    """Validate project structure and files."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def check_file_exists(self, file_path: str, description: str = None) -> bool:
        """Check if a file exists."""
        full_path = self.project_root / file_path
        exists = full_path.exists()
        
        desc = description or file_path
        status = "✅ PASS" if exists else "❌ FAIL"
        self.results.append(f"{status}: {desc}")
        
        if exists:
            self.passed += 1
        else:
            self.failed += 1
        
        return exists
    
    def check_directory_exists(self, dir_path: str, description: str = None) -> bool:
        """Check if a directory exists."""
        full_path = self.project_root / dir_path
        exists = full_path.is_dir()
        
        desc = description or dir_path
        status = "✅ PASS" if exists else "❌ FAIL"
        self.results.append(f"{status}: Directory '{desc}'")
        
        if exists:
            self.passed += 1
        else:
            self.failed += 1
        
        return exists
    
    def check_json_valid(self, file_path: str, description: str = None) -> bool:
        """Check if a JSON file is valid."""
        full_path = self.project_root / file_path
        
        try:
            if not full_path.exists():
                self.results.append(f"❌ FAIL: JSON file not found: {file_path}")
                self.failed += 1
                return False
            
            with open(full_path, 'r') as f:
                json.load(f)
            
            desc = description or file_path
            self.results.append(f"✅ PASS: Valid JSON - {desc}")
            self.passed += 1
            return True
        except json.JSONDecodeError as e:
            desc = description or file_path
            self.results.append(f"❌ FAIL: Invalid JSON - {desc} ({str(e)})")
            self.failed += 1
            return False
        except Exception as e:
            self.results.append(f"❌ FAIL: Error reading JSON - {file_path} ({str(e)})")
            self.failed += 1
            return False
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("=" * 70)
        print("PROJECT VALIDATION - Factory Compliance Monitoring System")
        print("=" * 70)
        print()
        
        # Project structure
        print("📁 PROJECT STRUCTURE")
        print("-" * 70)
        self.check_directory_exists("src", "Source code directory")
        self.check_directory_exists("src/core", "Core modules")
        self.check_directory_exists("src/detection", "Detection modules")
        self.check_directory_exists("src/database", "Database modules")
        self.check_directory_exists("src/severity", "Severity modules")
        self.check_directory_exists("src/dashboard", "Dashboard modules")
        self.check_directory_exists("src/reports", "Reports modules")
        self.check_directory_exists("data", "Data directory")
        self.check_directory_exists("outputs", "Outputs directory")
        print()
        
        # Python files - Core
        print("🐍 PYTHON FILES - CORE SYSTEM")
        print("-" * 70)
        self.check_file_exists("src/__init__.py", "Source package init")
        self.check_file_exists("src/main.py", "Main entry point")
        self.check_file_exists("src/core/__init__.py", "Core package init")
        self.check_file_exists("src/core/config_manager.py", "Configuration Manager")
        self.check_file_exists("src/core/event_bus.py", "Event Bus")
        self.check_file_exists("src/core/detector_manager.py", "Detector Manager")
        self.check_file_exists("src/core/system_stats.py", "System Statistics")
        print()
        
        # Python files - Detection
        print("🐍 PYTHON FILES - DETECTION")
        print("-" * 70)
        self.check_file_exists("src/detection/__init__.py", "Detection package init")
        self.check_file_exists("src/detection/base_detector.py", "Base Detector")
        self.check_file_exists("src/detection/walkway_detector_refactored.py", "Walkway Detector")
        self.check_file_exists("src/detection/unauthorized_intervention_detector_refactored.py", "Intervention Detector")
        print()
        
        # Python files - Database
        print("🐍 PYTHON FILES - DATABASE")
        print("-" * 70)
        self.check_file_exists("src/database/__init__.py", "Database package init")
        self.check_file_exists("src/database/db_manager.py", "Database Manager")
        self.check_file_exists("src/database/models.py", "Database Models")
        self.check_file_exists("src/database/database_service.py", "Database Service")
        print()
        
        # Python files - Other modules
        print("🐍 PYTHON FILES - OTHER MODULES")
        print("-" * 70)
        self.check_file_exists("src/severity/event_factory.py", "Event Factory")
        self.check_file_exists("src/dashboard/app.py", "Dashboard App")
        self.check_file_exists("src/reports/report_generator.py", "Report Generator")
        print()
        
        # Configuration files
        print("⚙️  CONFIGURATION FILES")
        print("-" * 70)
        self.check_file_exists("outputs/zones.json", "Zones Configuration")
        self.check_json_valid("outputs/zones.json", "zones.json validity")
        
        self.check_file_exists("outputs/validated_rules.json", "Rules Configuration")
        self.check_json_valid("outputs/validated_rules.json", "validated_rules.json validity")
        
        self.check_file_exists("requirements.txt", "Python Requirements")
        print()
        
        # Data files
        print("📹 DATA FILES")
        print("-" * 70)
        self.check_file_exists("yolov8n.pt", "YOLOv8 Model")
        print()
        
        # Output files
        print("📊 OUTPUT FILES")
        print("-" * 70)
        self.check_file_exists("outputs/compliance_logs.db", "SQLite Database")
        print()
        
        # Results summary
        print("=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        for result in self.results:
            print(result)
        
        print()
        print(f"✅ PASSED: {self.passed}")
        print(f"❌ FAILED: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        print()
        
        if self.failed == 0:
            print("🎉 ALL VALIDATION CHECKS PASSED!")
            print("=" * 70)
            return True
        else:
            print("⚠️  SOME VALIDATION CHECKS FAILED!")
            print("=" * 70)
            return False


def main():
    """Run project validation."""
    validator = ProjectValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
