import os
import json
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Read the extracted text from Step 1
    try:
        with open("outputs/policy_text.txt", "r", encoding="utf-8") as f:
            policy_text = f.read()
    except FileNotFoundError:
        print("❌ Error: outputs/policy_text.txt not found. Run pdf_parser.py first.")
        return

    print("Sending text to OpenAI for rule extraction...")
    
    # Using response_format to guarantee strict JSON output
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system", 
                "content": "You are a strict EHS compliance extraction system. You must output valid JSON. Extract the 4 main unsafe behaviors. For each behavior, use an identifiable snake_case string as the key. Each key must contain a nested object with the exact fields: 'observable_indicator', 'policy_reference', 'severity_hint', and 'threshold' (if applicable, e.g., for blocks)."
            },
            {
                "role": "user", 
                "content": f"Extract the rules from this policy text:\n\n{policy_text}"
            }
        ]
    )

    # Save the raw JSON safely
    rules_dict = json.loads(response.choices[0].message.content)
    
    with open("outputs/rules.json", "w") as f:
        json.dump(rules_dict, f, indent=4)
        
    print("✅ Successfully extracted and saved rules to outputs/rules.json")

if __name__ == "__main__":
    main()