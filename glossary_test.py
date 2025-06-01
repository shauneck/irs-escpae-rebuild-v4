import requests
import sys
import json
from datetime import datetime

class GlossaryAPITester:
    def __init__(self, base_url="https://990325ad-971f-441f-a0fd-260295cad6cf.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_content=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            status_success = response.status_code == expected_status
            
            if status_success:
                print(f"✅ Status check passed - Expected {expected_status}, got {response.status_code}")
            else:
                print(f"❌ Status check failed - Expected {expected_status}, got {response.status_code}")
                return False, {}
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
            except:
                response_data = {}
            
            # Check expected content if provided
            content_success = True
            if expected_content:
                for key, value in expected_content.items():
                    if key not in response_data or response_data[key] != value:
                        content_success = False
                        print(f"❌ Content check failed - Expected {key}={value}, got {response_data.get(key, 'missing')}")
            
            if content_success:
                self.tests_passed += 1
                print(f"✅ Test passed")
            
            return status_success and content_success, response_data

        except Exception as e:
            print(f"❌ Test failed - Error: {str(e)}")
            return False, {}

    def test_health(self):
        """Test API health endpoint"""
        return self.run_test(
            "API Health Check",
            "GET",
            "health",
            200,
            expected_content={"status": "ok"}
        )

    def test_get_glossary_terms(self):
        """Test getting all glossary terms"""
        success, response = self.run_test(
            "Get All Glossary Terms",
            "GET",
            "glossary",
            200
        )
        
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} glossary terms")
            
            # Check if the expected terms are in the glossary
            expected_terms = [
                "tax code", "wealth-building behavior", "CPAs", "Strategists", 
                "Tax strategists", "W-2 income", "tax planning", "Entity Type", 
                "entity structure", "Income Type", "Timing", "timing", 
                "asset rollovers", "Asset Location", "Deduction Strategy", 
                "deductions", "Exit Planning", "Business owners", "W-2 earners", 
                "Real estate professionals", "Exit events", "case studies", 
                "capital gains", "Qualified Opportunity Fund (QOF)", "STR", 
                "Retained earnings", "bonus depreciation", 
                "Real Estate Professional (REPS)", "depreciation offset", 
                "tax exposure", "AGI", "Income Type Stack", "Entity Exposure", 
                "Deduction Bandwidth"
            ]
            
            found_terms = [term.get('term', '') for term in response]
            missing_terms = [term for term in expected_terms if term.lower() not in [t.lower() for t in found_terms]]
            
            if missing_terms:
                print(f"⚠️ Missing expected terms: {', '.join(missing_terms)}")
            else:
                print(f"✅ All expected terms found in the glossary")
                
            return True, response
        return False, {}

    def test_get_glossary_term(self, term_id):
        """Test getting a specific glossary term"""
        return self.run_test(
            f"Get Glossary Term {term_id}",
            "GET",
            f"glossary/{term_id}",
            200
        )

    def test_get_module_content(self, module_id):
        """Test getting content for a specific module"""
        success, response = self.run_test(
            f"Get Module {module_id} Content",
            "GET",
            f"modules/{module_id}",
            200
        )
        
        if success:
            # Check if the module content contains glossary terms
            if 'content' in response:
                if '**' in response['content']:
                    print(f"✅ Module {module_id} content contains formatted glossary terms")
                else:
                    print(f"⚠️ Module {module_id} content may not have formatted glossary terms")
            return True, response
        return False, {}

def run_tests():
    # Setup
    tester = GlossaryAPITester()
    
    # Run tests
    print("\n=== Running API Tests for Glossary Functionality ===\n")
    
    # Test API health
    health_success, _ = tester.test_health()
    if not health_success:
        print("❌ API health check failed, stopping tests")
        return 1
    
    # Test getting all glossary terms
    glossary_success, glossary_terms = tester.test_get_glossary_terms()
    if not glossary_success:
        print("❌ Failed to retrieve glossary terms, stopping tests")
        return 1
    
    # Test getting a specific glossary term (if we have terms)
    if glossary_terms and len(glossary_terms) > 0:
        term_id = glossary_terms[0].get('id', '')
        if term_id:
            term_success, _ = tester.test_get_glossary_term(term_id)
            if not term_success:
                print(f"❌ Failed to retrieve specific glossary term {term_id}")
    
    # Test getting module content for all 4 modules
    for module_id in range(1, 5):
        module_success, _ = tester.test_get_module_content(module_id)
        if not module_success:
            print(f"❌ Failed to retrieve content for module {module_id}")
    
    # Print results
    print(f"\n📊 Tests run: {tester.tests_run}")
    print(f"📊 Tests passed: {tester.tests_passed}")
    print(f"📊 Tests failed: {tester.tests_run - tester.tests_passed}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n✅ All API tests passed successfully!")
        return 0
    else:
        print("\n❌ Some API tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())