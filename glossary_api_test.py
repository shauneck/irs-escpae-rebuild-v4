import requests
import sys
import json

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://2509541f-404c-4ef1-acc6-ed11dcdd6898.preview.emergentagent.com"

def test_glossary_api():
    """Test the glossary API endpoints and verify the expected terms"""
    api_url = f"{BACKEND_URL}/api"
    tests_passed = 0
    tests_run = 0
    
    print("\n=== Testing Glossary API ===\n")
    
    # Test 1: Get all glossary terms
    tests_run += 1
    try:
        response = requests.get(f"{api_url}/glossary")
        if response.status_code == 200:
            glossary_terms = response.json()
            print(f"✅ Retrieved {len(glossary_terms)} glossary terms")
            tests_passed += 1
            
            # Check for expected terms
            expected_terms = [
                "CPAs", "Strategists", "Tax strategists", "W-2 income", "tax planning",
                "entity structure", "Opportunity Zones", "asset location",
                "capital gains", "Qualified Opportunity Fund (QOF)", "STR", 
                "bonus depreciation", "Real Estate Professional (REPS)", "depreciation offset",
                "tax exposure", "AGI", "Income Type Stack", "Entity Exposure", "Deduction Bandwidth",
                "personalized planning", "Lever Hierarchy", "Strategy Stack", "Advisor Integration"
            ]
            
            found_terms = [term.get('term', '') for term in glossary_terms]
            print("\nFound glossary terms:")
            for term in found_terms:
                print(f"- {term}")
            
            missing_terms = [term for term in expected_terms if term.lower() not in [t.lower() for t in found_terms]]
            
            if missing_terms:
                print(f"\n⚠️ Missing expected terms: {', '.join(missing_terms)}")
            else:
                print(f"\n✅ All expected terms found in the glossary")
            
            # Check STR definition
            str_term = next((term for term in glossary_terms if term.get('term', '').lower() == 'str'), None)
            if str_term:
                print(f"\nSTR Definition: {str_term.get('definition', '')}")
                expected_str_def = "Short-Term Rental (STR): A property rented for an average stay of 7 days or less, qualifying for different tax treatment under IRC §469 and Treas. Reg. §1.469-1T(e)(3)."
                if expected_str_def.lower() in str_term.get('definition', '').lower():
                    print(f"✅ STR definition is correct")
                else:
                    print(f"❌ STR definition is incorrect")
                    print(f"Expected: {expected_str_def}")
            else:
                print(f"❌ STR term not found in glossary")
        else:
            print(f"❌ Failed to retrieve glossary terms: {response.status_code}")
    except Exception as e:
        print(f"❌ Error retrieving glossary terms: {str(e)}")
    
    # Test 2: Get module content for each module to check glossary term highlighting
    for module_id in range(1, 6):
        tests_run += 1
        try:
            response = requests.get(f"{api_url}/modules/{module_id}")
            if response.status_code == 200:
                module_data = response.json()
                print(f"\n=== Module {module_id}: {module_data.get('title', 'Unknown')} ===")
                tests_passed += 1
                
                # Check if content contains glossary term markup
                content = module_data.get('content', '')
                
                # Look for glossary-term class in the content
                if 'class="glossary-term"' in content:
                    print(f"✅ Module {module_id} has glossary term highlighting")
                    
                    # Count occurrences of glossary-term class
                    term_count = content.count('class="glossary-term"')
                    print(f"   Found {term_count} highlighted glossary terms")
                    
                    # Check for specific terms based on module
                    module_terms = {
                        1: ["CPAs", "Strategists", "Tax strategists", "W-2 income", "tax planning"],
                        2: ["entity structure", "Opportunity Zones", "asset location"],
                        3: ["capital gains", "Qualified Opportunity Fund (QOF)", "STR", "bonus depreciation", 
                            "Real Estate Professional (REPS)", "depreciation offset"],
                        4: ["tax exposure", "AGI", "Income Type Stack", "Entity Exposure", "Deduction Bandwidth"],
                        5: ["personalized planning", "Lever Hierarchy", "Strategy Stack", "Advisor Integration"]
                    }
                    
                    if module_id in module_terms:
                        for term in module_terms[module_id]:
                            if f'data-term="{term}"' in content:
                                print(f"   ✅ Term '{term}' is highlighted")
                            else:
                                print(f"   ❌ Term '{term}' is not highlighted")
                else:
                    print(f"❌ Module {module_id} has no glossary term highlighting")
                
                # Check for header highlighting (should not be highlighted)
                headers_with_highlights = []
                for header_tag in ['<h1', '<h2', '<h3', '<h4', '<h5', '<h6']:
                    if header_tag in content:
                        header_sections = content.split(header_tag)
                        for section in header_sections[1:]:  # Skip first split which is before any header
                            header_end = section.find('</h')
                            if header_end > 0:
                                header_content = section[:header_end]
                                if 'class="glossary-term"' in header_content:
                                    headers_with_highlights.append(header_content)
                
                if headers_with_highlights:
                    print(f"❌ Module {module_id} has {len(headers_with_highlights)} glossary terms highlighted in headers")
                else:
                    print(f"✅ Module {module_id} correctly avoids highlighting terms in headers")
                
                # Check for first occurrence only highlighting
                for term in module_terms.get(module_id, []):
                    term_count = content.count(f'data-term="{term}"')
                    if term_count > 1:
                        print(f"❌ Term '{term}' is highlighted {term_count} times (should be once)")
                    elif term_count == 1:
                        print(f"✅ Term '{term}' is correctly highlighted only once")
                    
                # Check for glossary-repeat class for subsequent occurrences
                if 'class="glossary-repeat"' in content:
                    repeat_count = content.count('class="glossary-repeat"')
                    print(f"✅ Module {module_id} has {repeat_count} subsequent term references with correct styling")
                else:
                    print(f"⚠️ Module {module_id} may not have proper styling for subsequent term references")
            else:
                print(f"❌ Failed to retrieve Module {module_id} content: {response.status_code}")
        except Exception as e:
            print(f"❌ Error retrieving Module {module_id} content: {str(e)}")
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_run - tests_passed}")
    
    return tests_passed == tests_run

if __name__ == "__main__":
    success = test_glossary_api()
    sys.exit(0 if success else 1)