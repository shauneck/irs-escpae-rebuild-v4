
import requests
import sys
import json
from pprint import pprint

class CourseAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status=200, data=None, expected_data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
            status_success = response.status_code == expected_status
            
            if status_success:
                print(f"✅ Status check passed - Expected: {expected_status}, Got: {response.status_code}")
            else:
                print(f"❌ Status check failed - Expected: {expected_status}, Got: {response.status_code}")
                return False, None
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except Exception as e:
                print(f"❌ Failed to parse JSON response: {str(e)}")
                print(f"Response text: {response.text[:200]}...")
                return False, None
            
            # If expected data is provided, check it
            data_success = True
            if expected_data:
                for key, value in expected_data.items():
                    if isinstance(response_data, list):
                        # For list responses, check if any item contains the expected value
                        found = False
                        for item in response_data:
                            if key in item and item[key] == value:
                                found = True
                                break
                        if not found:
                            print(f"❌ Data check failed - Expected {key}={value} not found in list response")
                            data_success = False
                    elif key in response_data:
                        if response_data[key] != value:
                            print(f"❌ Data check failed - Expected {key}={value}, Got {key}={response_data[key]}")
                            data_success = False
                    else:
                        print(f"❌ Data check failed - Key {key} not found in response")
                        data_success = False
            
            if data_success:
                print(f"✅ Data check passed")
                self.tests_passed += 1
                return True, response_data
            else:
                return False, response_data

        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return False, None

    def test_get_all_courses(self):
        """Test getting all courses"""
        return self.run_test(
            "Get All Courses",
            "GET",
            "courses",
            expected_data={"title": "W-2 Escape Plan"}
        )

    def test_get_w2_course(self, course_id):
        """Test getting W-2 course details"""
        return self.run_test(
            "Get W-2 Course Details",
            "GET",
            f"courses/{course_id}",
            expected_data={"title": "W-2 Escape Plan", "total_lessons": 4}
        )

    def test_get_w2_lessons(self, course_id):
        """Test getting W-2 course lessons"""
        success, data = self.run_test(
            "Get W-2 Course Lessons",
            "GET",
            f"courses/{course_id}/lessons"
        )
        
        if success and data:
            # Check if we have 4 modules
            if len(data) != 4:
                print(f"❌ Expected 4 modules, got {len(data)}")
                return False, data
            
            # Check if Module 4 exists
            module4 = None
            for module in data:
                if module.get("order_index") == 4:
                    module4 = module
                    break
            
            if not module4:
                print("❌ Module 4 not found in lessons")
                return False, data
            
            # Check Module 4 details
            if module4.get("title") != "Qualifying for REPS — The Gateway to Strategic Offsets":
                print(f"❌ Module 4 title mismatch: {module4.get('title')}")
                return False, data
            
            if module4.get("description") != "Module 4 of 8 - REPS Qualification - Master Real Estate Professional Status requirements and unlock active loss treatment for your investments":
                print(f"❌ Module 4 description mismatch")
                return False, data
            
            if module4.get("duration_minutes") != 60:
                print(f"❌ Module 4 duration mismatch: {module4.get('duration_minutes')}")
                return False, data
            
            print("✅ Module 4 details verified successfully")
            return True, data
        
        return False, data

    def test_get_module4_quiz(self, course_id):
        """Test getting Module 4 quiz questions"""
        success, data = self.run_test(
            "Get Module 4 Quiz Questions",
            "GET",
            f"courses/{course_id}/quiz?module_id=4"
        )
        
        if success and data:
            # Check if we have 3 questions
            if len(data) != 3:
                print(f"❌ Expected 3 quiz questions, got {len(data)}")
                return False, data
            
            # Check if each question is worth 50 points
            for question in data:
                if question.get("points") != 50:
                    print(f"❌ Expected 50 points per question, got {question.get('points')}")
                    return False, data
            
            # Check if the questions match the expected content
            expected_questions = [
                "What is the primary benefit of Real Estate Professional Status (REPS) for W-2 earners?",
                "What are the two requirements of the IRS Time Test for REPS qualification?",
                "In Helen's Year 3 case study, how did she achieve REPS qualification while maintaining her W-2 job?"
            ]
            
            for question in data:
                if question.get("question") not in expected_questions:
                    print(f"❌ Unexpected quiz question: {question.get('question')}")
                    return False, data
            
            print("✅ Module 4 quiz questions verified successfully")
            return True, data
        
        return False, data

    def test_get_glossary_terms(self):
        """Test getting glossary terms"""
        success, data = self.run_test(
            "Get Glossary Terms",
            "GET",
            "glossary"
        )
        
        if success and data:
            # Check if REPS-related terms exist
            expected_terms = [
                "Real Estate Professional Status (REPS)",
                "Material Participation",
                "Passive Loss Limitation",
                "Active vs Passive Income",
                "IRS Time Test"
            ]
            
            found_terms = []
            for term in data:
                if term.get("term") in expected_terms:
                    found_terms.append(term.get("term"))
            
            if len(found_terms) < len(expected_terms):
                missing_terms = set(expected_terms) - set(found_terms)
                print(f"❌ Missing glossary terms: {missing_terms}")
                return False, data
            
            print("✅ REPS-related glossary terms verified successfully")
            return True, data
        
        return False, data

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        if self.tests_passed == self.tests_run:
            print("✅ All backend tests passed!")
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")

def main():
    # Get the backend URL from the frontend .env file
    import os
    
    # Read the backend URL from the frontend .env file
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if 'REACT_APP_BACKEND_URL' in line:
                backend_url = line.strip().split('=')[1]
                break
    
    print(f"Using backend URL: {backend_url}")
    
    # Initialize the tester
    tester = CourseAPITester(backend_url)
    
    # Test getting all courses
    success, courses_data = tester.test_get_all_courses()
    if not success:
        print("❌ Failed to get courses, stopping tests")
        tester.print_summary()
        return 1
    
    # Find the W-2 course ID
    w2_course_id = None
    for course in courses_data:
        if course.get("title") == "W-2 Escape Plan":
            w2_course_id = course.get("id")
            break
    
    if not w2_course_id:
        print("❌ W-2 Escape Plan course not found, stopping tests")
        tester.print_summary()
        return 1
    
    print(f"Found W-2 course ID: {w2_course_id}")
    
    # Test getting W-2 course details
    success, _ = tester.test_get_w2_course(w2_course_id)
    if not success:
        print("❌ Failed to get W-2 course details")
    
    # Test getting W-2 course lessons
    success, _ = tester.test_get_w2_lessons(w2_course_id)
    if not success:
        print("❌ Failed to verify W-2 course lessons")
    
    # Test getting Module 4 quiz questions
    success, _ = tester.test_get_module4_quiz(w2_course_id)
    if not success:
        print("❌ Failed to verify Module 4 quiz questions")
    
    # Test getting glossary terms
    success, _ = tester.test_get_glossary_terms()
    if not success:
        print("❌ Failed to verify glossary terms")
    
    # Print summary
    tester.print_summary()
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      