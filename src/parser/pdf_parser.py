import fitz
import os

def main():
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    pdf_path = "data/policy/Compliance_Policy_Manual.pdf"
    
    print(f"Opening PDF: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
            
        with open("outputs/policy_text.txt", "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print("✅ Successfully extracted policy text to outputs/policy_text.txt")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find {pdf_path}. Please ensure the document is in the correct directory.")
    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")

if __name__ == "__main__":
    main()