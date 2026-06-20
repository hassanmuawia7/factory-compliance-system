"""
Configuration Manager
Centralizes loading and access to all system configurations.

This module ensures:
1. Configs are loaded ONCE at startup
2. All modules access configs through this single interface
3. Graceful handling of missing files
4. Type-safe config access
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Rule:
    """Represents a single compliance rule."""
    name: str
    observable_indicator: str
    policy_reference: str
    severity_hint: str
    threshold: Optional[int] = None


class ConfigManager:
    """Centralized configuration manager for the compliance system."""
    
    _instance = None  # Singleton pattern
    
    def __init__(self, config_dir: str = "outputs"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing zones.json and validated_rules.json
        """
        self.config_dir = config_dir
        self._zones_data: Dict[str, Any] = {}
        self._rules_data: Dict[str, Rule] = {}
        self._load_configs()
    
    @classmethod
    def get_instance(cls, config_dir: str = "outputs") -> "ConfigManager":
        """Get singleton instance of ConfigManager."""
        if cls._instance is None:
            cls._instance = cls(config_dir)
        return cls._instance
    
    def _load_configs(self) -> None:
        """Load both configuration files at startup."""
        self._load_zones()
        self._load_rules()
    
    def _load_zones(self) -> None:
        """Load zones.json file."""
        zones_path = os.path.join(self.config_dir, "zones.json")
        
        try:
            with open(zones_path, "r") as f:
                self._zones_data = json.load(f)
            print(f"✅ Zones loaded from {zones_path}")
        except FileNotFoundError:
            print(f"⚠️  zones.json not found at {zones_path}")
            print("   Using default configurations")
            self._zones_data = self._get_default_zones()
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {zones_path}")
            self._zones_data = self._get_default_zones()
    
    def _load_rules(self) -> None:
        """Load validated_rules.json file."""
        rules_path = os.path.join(self.config_dir, "validated_rules.json")
        
        try:
            with open(rules_path, "r") as f:
                rules_json = json.load(f)
            
            # Convert to Rule objects
            for rule_name, rule_data in rules_json.items():
                self._rules_data[rule_name] = Rule(
                    name=rule_name,
                    observable_indicator=rule_data.get("observable_indicator", ""),
                    policy_reference=rule_data.get("policy_reference", ""),
                    severity_hint=rule_data.get("severity_hint", "LOW"),
                    threshold=rule_data.get("threshold")
                )
            
            print(f"✅ Rules loaded from {rules_path} ({len(self._rules_data)} rules)")
        
        except FileNotFoundError:
            print(f"⚠️  validated_rules.json not found at {rules_path}")
            print("   Using default rules")
            self._rules_data = self._get_default_rules()
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {rules_path}")
            self._rules_data = self._get_default_rules()
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """
        Get rule by name.
        
        Args:
            rule_name: Name of the rule (e.g., 'walkway_violation')
        
        Returns:
            Rule object or None if not found
        """
        return self._rules_data.get(rule_name)
    
    def get_all_rules(self) -> Dict[str, Rule]:
        """Get all loaded rules."""
        return self._rules_data.copy()
    
    def get_walkway_zone(self) -> List[List[int]]:
        """
        Get the walkway safe zone.
        
        Returns:
            List of coordinates: [[x1, y1], [x2, y2], ...]
        """
        if "walkway_zone" in self._zones_data:
            return self._zones_data["walkway_zone"]
        return self._get_default_zones()["walkway_zone"]
    
    def get_machinery_zones(self) -> Dict[str, List[List[int]]]:
        """
        Get all machinery danger zones.
        
        Returns:
            Dict mapping zone name to list of coordinates
        """
        if "machinery_zones" in self._zones_data:
            return self._zones_data["machinery_zones"]
        return self._get_default_zones()["machinery_zones"]
    
    def get_machinery_zone(self, zone_name: str) -> Optional[List[List[int]]]:
        """
        Get specific machinery zone by name.
        
        Args:
            zone_name: Name of the machinery zone
        
        Returns:
            List of coordinates or None if not found
        """
        zones = self.get_machinery_zones()
        return zones.get(zone_name)
    
    def get_all_zones(self) -> Dict[str, Any]:
        """Get all loaded zones."""
        return self._zones_data.copy()
    
    @staticmethod
    def _get_default_zones() -> Dict[str, Any]:
        """Get default zone configuration."""
        return {
            "walkway_zone": [
                [100, 100], [500, 100],
                [500, 400], [100, 400]
            ],
            "machinery_zones": {
                "machine_1": [
                    [600, 400], [1000, 400],
                    [1000, 800], [600, 800]
                ]
            }
        }
    
    @staticmethod
    def _get_default_rules() -> Dict[str, Rule]:
        """Get default rule configuration."""
        return {
            "walkway_violation": Rule(
                name="walkway_violation",
                observable_indicator="person outside walkway zone",
                policy_reference="POLICY_WALKWAY_001",
                severity_hint="HIGH"
            ),
            "unauthorized_intervention": Rule(
                name="unauthorized_intervention",
                observable_indicator="person without safety vest in machinery zone",
                policy_reference="POLICY_SAFETY_002",
                severity_hint="CRITICAL"
            )
        }
    
    def validate(self) -> bool:
        """
        Validate that configuration is loaded and usable.
        
        Returns:
            True if valid configuration
        """
        has_rules = len(self._rules_data) > 0
        has_zones = len(self._zones_data) > 0
        
        if not has_rules or not has_zones:
            print("❌ Configuration validation failed")
            return False
        
        print(f"✅ Configuration valid: {len(self._rules_data)} rules, {len(self._zones_data)} zone groups")
        return True


# Module-level convenience functions
def get_config() -> ConfigManager:
    """Get the global ConfigManager instance."""
    return ConfigManager.get_instance()


if __name__ == "__main__":
    # Test the ConfigManager
    config = ConfigManager("outputs")
    print("\n📋 Configuration Report:")
    print(f"Walkway zone: {len(config.get_walkway_zone())} points")
    print(f"Machinery zones: {list(config.get_machinery_zones().keys())}")
    print(f"Rules: {list(config.get_all_rules().keys())}")
    
    walkway_rule = config.get_rule("walkway_violation")
    if walkway_rule:
        print(f"\nWalkway Rule:")
        print(f"  Policy: {walkway_rule.policy_reference}")
        print(f"  Severity: {walkway_rule.severity_hint}")
