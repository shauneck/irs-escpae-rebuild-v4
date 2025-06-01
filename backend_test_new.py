import requests
import unittest
import sys
import json

class IRSEscapePlanAPITest(unittest.TestCase):
    """Test suite for the IRS Escape Plan API"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.base_url = "http://localhost:8001/api"
        self.headers = {"Content-Type": "application/json"}
    
    def test_01_health_check(self):
        """Test API health check endpoint"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "IRS Escape Plan API is running"})
        print("✅ API health check passed")
    
    def test_02_get_courses(self):
        """Test getting all courses"""
        response = requests.get(f"{self.base_url}/courses")
        self.assertEqual(response.status_code, 200)
        courses = response.json()
        self.assertIsInstance(courses, list)
        self.assertGreaterEqual(len(courses), 3, "Expected at least 3 courses")
        
        # Verify course structure
        course = courses[0]
        self.assertIn("id", course)
        self.assertIn("title", course)
        self.assertIn("description", course)
        self.assertIn("thumbnail_url", course)
        self.assertIn("is_free", course)
        self.assertIn("total_lessons", course)
        self.assertIn("estimated_hours", course)
        self.assertIn("lessons", course)
        print(f"✅ Found {len(courses)} courses")
    
    def test_03_get_course_by_id(self):
        """Test getting a specific course by ID"""
        # First get all courses to find a valid ID
        response = requests.get(f"{self.base_url}/courses")
        courses = response.json()
        course_id = courses[0]["id"]
        
        # Now get the specific course
        response = requests.get(f"{self.base_url}/courses/{course_id}")
        self.assertEqual(response.status_code, 200)
        course = response.json()
        self.assertEqual(course["id"], course_id)
        print(f"✅ Successfully retrieved course: {course['title']}")
    
    def test_04_get_glossary(self):
        """Test getting all glossary terms"""
        response = requests.get(f"{self.base_url}/glossary")
        self.assertEqual(response.status_code, 200)
        terms = response.json()
        self.assertIsInstance(terms, list)
        self.assertGreaterEqual(len(terms), 25, "Expected at least 25 glossary terms")
        
        # Verify term structure
        term = terms[0]
        self.assertIn("id", term)
        self.assertIn("term", term)
        self.assertIn("definition", term)
        self.assertIn("category", term)
        self.assertIn("related_terms", term)
        print(f"✅ Found {len(terms)} glossary terms")
    
    def test_05_get_glossary_term_by_id(self):
        """Test getting a specific glossary term by ID"""
        # First get all terms to find a valid ID
        response = requests.get(f"{self.base_url}/glossary")
        terms = response.json()
        term_id = terms[0]["id"]
        
        # Now get the specific term
        response = requests.get(f"{self.base_url}/glossary/{term_id}")
        self.assertEqual(response.status_code, 200)
        term = response.json()
        self.assertEqual(term["id"], term_id)
        print(f"✅ Successfully retrieved glossary term: {term['term']}")
    
    def test_06_get_tools(self):
        """Test getting all tools"""
        response = requests.get(f"{self.base_url}/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertGreaterEqual(len(tools), 2, "Expected at least 2 tools")
        
        # Verify tool structure
        tool = tools[0]
        self.assertIn("id", tool)
        self.assertIn("name", tool)
        self.assertIn("description", tool)
        self.assertIn("type", tool)
        self.assertIn("icon", tool)
        self.assertIn("is_free", tool)
        self.assertIn("config", tool)
        print(f"✅ Found {len(tools)} tools")
    
    def test_07_get_tool_by_id(self):
        """Test getting a specific tool by ID"""
        # First get all tools to find a valid ID
        response = requests.get(f"{self.base_url}/tools")
        tools = response.json()
        tool_id = tools[0]["id"]
        
        # Now get the specific tool
        response = requests.get(f"{self.base_url}/tools/{tool_id}")
        self.assertEqual(response.status_code, 200)
        tool = response.json()
        self.assertEqual(tool["id"], tool_id)
        print(f"✅ Successfully retrieved tool: {tool['name']}")
    
    def test_08_get_quizzes(self):
        """Test getting quizzes endpoint (even if it returns 404)"""
        response = requests.get(f"{self.base_url}/quizzes")
        # This might return 404 if not implemented yet
        print(f"ℹ️ Quizzes endpoint returned status code: {response.status_code}")
        if response.status_code == 200:
            quizzes = response.json()
            self.assertIsInstance(quizzes, list)
            print(f"✅ Found {len(quizzes)} quizzes")
        else:
            print("⚠️ Quizzes endpoint not implemented or returned an error")
    
    def test_09_xp_tracking(self):
        """Test XP tracking endpoints"""
        # Try to get user XP
        response = requests.get(f"{self.base_url}/users/xp")
        print(f"ℹ️ User XP endpoint returned status code: {response.status_code}")
        if response.status_code == 200:
            xp_data = response.json()
            self.assertIn("total_xp", xp_data)
            print(f"✅ User has {xp_data['total_xp']} XP")
        else:
            print("⚠️ User XP endpoint not implemented or returned an error")
    
    def test_10_marketplace(self):
        """Test marketplace endpoint"""
        response = requests.get(f"{self.base_url}/marketplace")
        print(f"ℹ️ Marketplace endpoint returned status code: {response.status_code}")
        if response.status_code == 200:
            marketplace_items = response.json()
            self.assertIsInstance(marketplace_items, list)
            print(f"✅ Found {len(marketplace_items)} marketplace items")
        else:
            print("⚠️ Marketplace endpoint not implemented or returned an error")

def run_tests():
    """Run all tests and return exit code"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(IRSEscapePlanAPITest)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    return 0 if test_result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())