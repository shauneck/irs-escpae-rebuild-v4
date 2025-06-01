import requests
import unittest
import json
import uuid
import os
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://2f7b5da6-4045-4afb-968b-f13543c0575b.preview.emergentagent.com"

class IRSEscapePlanAPITest(unittest.TestCase):
    """Test suite for the IRS Escape Plan API"""

    def setUp(self):
        """Initialize test data"""
        self.api_url = f"{BACKEND_URL}/api"
        self.test_user_id = str(uuid.uuid4())
        self.courses = []
        self.tools = []
        self.glossary_terms = []
        self.marketplace_items = []
        
        # Initialize test data
        self.initialize_data()
        
    def initialize_data(self):
        """Initialize sample data in the database"""
        try:
            response = requests.post(f"{self.api_url}/initialize-data")
            self.assertEqual(response.status_code, 200)
            print("✅ Sample data initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize data: {str(e)}")
            sys.exit(1)
    
    def test_01_health_check(self):
        """Test the API health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["message"], "IRS Escape Plan API is running")
            print("✅ API health check passed")
        except Exception as e:
            print(f"❌ API health check failed: {str(e)}")
            raise
    
    def test_02_get_courses(self):
        """Test getting all courses"""
        try:
            response = requests.get(f"{self.api_url}/courses")
            self.assertEqual(response.status_code, 200)
            self.courses = response.json()
            self.assertGreaterEqual(len(self.courses), 1)
            print(f"✅ Retrieved {len(self.courses)} courses")
            
            # Verify course structure
            course = self.courses[0]
            required_fields = ["id", "type", "title", "description", "thumbnail_url", 
                              "is_free", "total_lessons", "estimated_hours"]
            for field in required_fields:
                self.assertIn(field, course)
                
            # Verify at least one free course exists
            free_courses = [c for c in self.courses if c["is_free"]]
            self.assertGreaterEqual(len(free_courses), 1)
            print(f"✅ Found {len(free_courses)} free courses")
            
            # Verify course names match the expected names
            expected_course_names = {
                "primer": "The Escape Blueprint",
                "w2": "W-2 Escape Plan",
                "business": "Business Owner Escape Plan"
            }
            
            for course_type, expected_name in expected_course_names.items():
                course = next((c for c in self.courses if c["type"] == course_type), None)
                if course:
                    self.assertEqual(course["title"], expected_name, 
                                    f"Course of type '{course_type}' has incorrect name: '{course['title']}' (expected: '{expected_name}')")
                    print(f"✅ Verified course name: {course['title']}")
                else:
                    print(f"⚠️ Course of type '{course_type}' not found")
                    
        except Exception as e:
            print(f"❌ Get courses test failed: {str(e)}")
            raise
    
    def test_03_get_course_by_id(self):
        """Test getting a specific course by ID"""
        if not self.courses:
            self.test_02_get_courses()
        
        try:
            course_id = self.courses[0]["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}")
            self.assertEqual(response.status_code, 200)
            course = response.json()
            self.assertEqual(course["id"], course_id)
            print(f"✅ Retrieved course: {course['title']}")
        except Exception as e:
            print(f"❌ Get course by ID test failed: {str(e)}")
            raise
    
    def test_04_get_course_lessons(self):
        """Test getting lessons for a specific course"""
        if not self.courses:
            self.test_02_get_courses()
        
        try:
            course_id = self.courses[0]["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}/lessons")
            self.assertEqual(response.status_code, 200)
            lessons = response.json()
            self.assertGreaterEqual(len(lessons), 1)
            print(f"✅ Retrieved {len(lessons)} lessons for course {course_id}")
            
            # Verify lesson structure
            lesson = lessons[0]
            required_fields = ["id", "title", "description", "content", "duration_minutes", "order_index"]
            for field in required_fields:
                self.assertIn(field, lesson)
        except Exception as e:
            print(f"❌ Get course lessons test failed: {str(e)}")
            raise
    
    def test_05_get_course_quiz(self):
        """Test getting quiz questions for a specific course"""
        if not self.courses:
            self.test_02_get_courses()
        
        try:
            # Use the free primer course which should have quiz questions
            primer_course = next((c for c in self.courses if c["type"] == "primer"), None)
            if not primer_course:
                print("⚠️ No primer course found, using first course")
                primer_course = self.courses[0]
                
            course_id = primer_course["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}/quiz")
            self.assertEqual(response.status_code, 200)
            questions = response.json()
            
            # There might not be quiz questions for every course
            if questions:
                print(f"✅ Retrieved {len(questions)} quiz questions for course {course_id}")
                
                # Verify question structure
                question = questions[0]
                required_fields = ["id", "question", "type", "options", "correct_answer", "explanation"]
                for field in required_fields:
                    self.assertIn(field, question)
            else:
                print(f"⚠️ No quiz questions found for course {course_id}")
        except Exception as e:
            print(f"❌ Get course quiz test failed: {str(e)}")
            raise
    
    def test_06_submit_quiz_answer(self):
        """Test submitting a quiz answer"""
        if not self.courses:
            self.test_02_get_courses()
        
        try:
            # Use the free primer course which should have quiz questions
            primer_course = next((c for c in self.courses if c["type"] == "primer"), None)
            if not primer_course:
                print("⚠️ No primer course found, using first course")
                primer_course = self.courses[0]
                
            course_id = primer_course["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}/quiz")
            
            if response.status_code == 200:
                questions = response.json()
                if questions:
                    question = questions[0]
                    question_id = question["id"]
                    correct_answer = question["correct_answer"]
                    
                    # Test with correct answer
                    response = requests.post(
                        f"{self.api_url}/quiz/submit",
                        params={"course_id": course_id, "question_id": question_id, "answer": correct_answer}
                    )
                    self.assertEqual(response.status_code, 200)
                    result = response.json()
                    self.assertTrue(result["correct"])
                    self.assertGreater(result["points"], 0)
                    print(f"✅ Submitted correct quiz answer successfully")
                    
                    # Test with incorrect answer
                    wrong_answer = "Wrong Answer"
                    response = requests.post(
                        f"{self.api_url}/quiz/submit",
                        params={"course_id": course_id, "question_id": question_id, "answer": wrong_answer}
                    )
                    self.assertEqual(response.status_code, 200)
                    result = response.json()
                    self.assertFalse(result["correct"])
                    self.assertEqual(result["points"], 0)
                    print(f"✅ Submitted incorrect quiz answer successfully")
                else:
                    print(f"⚠️ No quiz questions found for course {course_id}, skipping test")
            else:
                print(f"⚠️ Failed to get quiz questions, skipping test")
        except Exception as e:
            print(f"❌ Submit quiz answer test failed: {str(e)}")
            raise
    
    def test_07_get_glossary(self):
        """Test getting all glossary terms"""
        try:
            response = requests.get(f"{self.api_url}/glossary")
            self.assertEqual(response.status_code, 200)
            self.glossary_terms = response.json()
            self.assertGreaterEqual(len(self.glossary_terms), 1)
            print(f"✅ Retrieved {len(self.glossary_terms)} glossary terms")
            
            # Verify glossary term structure
            term = self.glossary_terms[0]
            required_fields = ["id", "term", "definition", "category", "related_terms"]
            for field in required_fields:
                self.assertIn(field, term)
        except Exception as e:
            print(f"❌ Get glossary test failed: {str(e)}")
            raise
    
    def test_08_search_glossary(self):
        """Test searching glossary terms"""
        if not self.glossary_terms:
            self.test_07_get_glossary()
        
        try:
            # Use a term from the first glossary entry
            if self.glossary_terms:
                search_term = self.glossary_terms[0]["term"][:4]  # Use first few characters
                response = requests.get(f"{self.api_url}/glossary/search", params={"q": search_term})
                self.assertEqual(response.status_code, 200)
                results = response.json()
                self.assertGreaterEqual(len(results), 1)
                print(f"✅ Search for '{search_term}' returned {len(results)} results")
            else:
                print("⚠️ No glossary terms found, skipping test")
        except Exception as e:
            print(f"❌ Search glossary test failed: {str(e)}")
            raise
    
    def test_09_get_tools(self):
        """Test getting all tools"""
        try:
            response = requests.get(f"{self.api_url}/tools")
            self.assertEqual(response.status_code, 200)
            self.tools = response.json()
            self.assertGreaterEqual(len(self.tools), 1)
            print(f"✅ Retrieved {len(self.tools)} tools")
            
            # Verify tool structure
            tool = self.tools[0]
            required_fields = ["id", "name", "description", "type", "icon", "is_free"]
            for field in required_fields:
                self.assertIn(field, tool)
                
            # Verify at least one free tool exists
            free_tools = [t for t in self.tools if t["is_free"]]
            self.assertGreaterEqual(len(free_tools), 1)
            print(f"✅ Found {len(free_tools)} free tools")
        except Exception as e:
            print(f"❌ Get tools test failed: {str(e)}")
            raise
    
    def test_10_get_tool_by_id(self):
        """Test getting a specific tool by ID"""
        if not self.tools:
            self.test_09_get_tools()
        
        try:
            if self.tools:
                tool_id = self.tools[0]["id"]
                response = requests.get(f"{self.api_url}/tools/{tool_id}")
                self.assertEqual(response.status_code, 200)
                tool = response.json()
                self.assertEqual(tool["id"], tool_id)
                print(f"✅ Retrieved tool: {tool['name']}")
            else:
                print("⚠️ No tools found, skipping test")
        except Exception as e:
            print(f"❌ Get tool by ID test failed: {str(e)}")
            raise
    
    def test_11_update_progress(self):
        """Test updating user progress"""
        if not self.courses:
            self.test_02_get_courses()
        
        try:
            if self.courses and self.courses[0]["lessons"]:
                course_id = self.courses[0]["id"]
                lesson_id = self.courses[0]["lessons"][0]["id"]
                
                # Create progress data
                progress_data = {
                    "user_id": self.test_user_id,
                    "course_id": course_id,
                    "lesson_id": lesson_id,
                    "completed": True,
                    "score": 100
                }
                
                response = requests.post(f"{self.api_url}/progress", json=progress_data)
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["status"], "success")
                print(f"✅ Updated user progress successfully")
            else:
                print("⚠️ No courses or lessons found, skipping test")
        except Exception as e:
            print(f"❌ Update progress test failed: {str(e)}")
            raise
    
    def test_12_get_user_progress(self):
        """Test getting user progress"""
        # First, make sure we have some progress data
        self.test_11_update_progress()
        
        try:
            response = requests.get(f"{self.api_url}/progress/{self.test_user_id}")
            self.assertEqual(response.status_code, 200)
            progress = response.json()
            self.assertGreaterEqual(len(progress), 1)
            print(f"✅ Retrieved {len(progress)} progress records for user")
            
            # Verify progress structure
            if progress:
                record = progress[0]
                required_fields = ["user_id", "course_id", "lesson_id", "completed"]
                for field in required_fields:
                    self.assertIn(field, record)
        except Exception as e:
            print(f"❌ Get user progress test failed: {str(e)}")
            raise

def run_tests():
    """Run all tests and print a summary"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(IRSEscapePlanAPITest)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {test_result.testsRun}")
    print(f"Passed: {test_result.testsRun - len(test_result.failures) - len(test_result.errors)}")
    print(f"Failed: {len(test_result.failures)}")
    print(f"Errors: {len(test_result.errors)}")
    
    if test_result.failures or test_result.errors:
        print("\n=== FAILED TESTS ===")
        for test, error in test_result.failures + test_result.errors:
            print(f"- {test.id()}")
        return 1
    else:
        print("\n✅ All API tests passed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())
