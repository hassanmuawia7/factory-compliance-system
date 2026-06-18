import json
import os

def validate_rules(rules):
    """
    Validates the extracted JSON to ensure no LLM hallucinations
    or missing critical fields broke the schema.
    """
    required_fields = [
        "observable_indicator",
        "policy_reference",
        "severity_hint"
    ]
    
    print("Validating extracted rules structure...")
    
    for rule_name, rule_data in rules.items():
        print(f" -> Checking '{rule_name}'...")
        for field in required_fields:
            if field not in rule_data:
                raise ValueError(f"❌ Validation Failed: '{rule_name}' is missing the required field '{field}'")
                
        # Optional: Validate severity hints match our expected matrix
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if rule_data.get("severity_hint") not in valid_severities:
            print(f"   ⚠️ Warning: '{rule_name}' has unusual severity '{rule_data.get('severity_hint')}'. Double check this.")
            
    print("✅ All rules validated successfully!")
    return True

def main():
    try:
        with open("outputs/rules.json", "r") as f:
            rules = json.load(f)
            
        if validate_rules(rules):
            with open("outputs/validated_rules.json", "w") as f:
                json.dump(rules, f, indent=4)
            print("✅ Saved final validated schema to outputs/validated_rules.json")
            
    except FileNotFoundError:
        print("❌ Error: outputs/rules.json not found. Run rule_extractor.py first.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()