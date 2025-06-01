import requests
import unittest
import json
import uuid
import os
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://9fa09691-ae14-4c36-b3bb-c36b68d2573b.preview.emergentagent.com"

class Module5Test(unittest.TestCase):
    """Test suite for Module 5 of The Escape Blueprint course"""

    def setUp(self):
        """Initialize test data"""
        self.api_url = f"{BACKEND_URL}/api"
        self.test_user_id = str(uuid.uuid4())
        self.courses = []
        self.primer_course = None
        self.module5 = None
        self.glossary_terms = []
        self.module5_quiz_questions = []
        
        # Initialize test data
        self.initialize_data()
        
    def initialize_data(self):
        """Initialize sample data in the database"""
        try:
            response = requests.post(f"{self.api_url}/initialize-data")
            self.assertEqual(response.status_code, 200)
            print("✅ Sample data initialized successfully")
            
            # Get courses
            response = requests.get(f"{self.api_url}/courses")
            self.assertEqual(response.status_code, 200)
            self.courses = response.json()
            
            # Find the primer course
            self.primer_course = next((c for c in self.courses if c["type"] == "primer"), None)
            if not self.primer_course:
                print("❌ Primer course not found")
                sys.exit(1)
                
            # Get course lessons
            response = requests.get(f"{self.api_url}/courses/{self.primer_course['id']}/lessons")
            self.assertEqual(response.status_code, 200)
            lessons = response.json()
            
            # Find Module 5
            self.module5 = next((l for l in lessons if l["order_index"] == 5), None)
            if not self.module5:
                print("❌ Module 5 not found")
                sys.exit(1)
                
            # Get glossary terms
            response = requests.get(f"{self.api_url}/glossary")
            self.assertEqual(response.status_code, 200)
            self.glossary_terms = response.json()
            
            # Get Module 5 quiz questions
            response = requests.get(f"{self.api_url}/courses/{self.primer_course['id']}/quiz?module_id=5")
            self.assertEqual(response.status_code, 200)
            self.module5_quiz_questions = response.json()
            
        except Exception as e:
            print(f"❌ Failed to initialize data: {str(e)}")
            sys.exit(1)
    
    def test_01_course_total_lessons(self):
        """Test that the course now shows 9 total lessons"""
        try:
            self.assertEqual(self.primer_course["total_lessons"], 9)
            print(f"✅ Course shows {self.primer_course['total_lessons']} total lessons")
        except Exception as e:
            print(f"❌ Course total lessons test failed: {str(e)}")
            raise
    
    def test_02_module5_exists(self):
        """Test that Module 5 exists and has the correct subtitle"""
        try:
            self.assertIsNotNone(self.module5)
            self.assertEqual(self.module5["title"], "Building Your Custom Escape Plan")
            self.assertEqual(self.module5["description"], "Module 5 of 5 - Create your personalized tax escape plan using the 6 levers, case studies, and strategic framework")
            print(f"✅ Module 5 exists with correct title and subtitle")
        except Exception as e:
            print(f"❌ Module 5 existence test failed: {str(e)}")
            raise
    
    def test_03_module5_content(self):
        """Test that Module 5 content includes all required sections"""
        try:
            content = self.module5["content"]
            
            # Check for required sections
            required_sections = [
                "Profile Assessment",
                "W-2 Dominant",
                "Business Owner",
                "Investor/Hybrid",
                "Lever Hierarchy",
                "Strategy Stack",
                "Foundation Layer",
                "Growth Layer",
                "Advanced Layer",
                "Implementation Timeline",
                "Year 1",
                "Year 2-3",
                "Year 3+",
                "Advisor Integration",
                "DIY Appropriate",
                "Strategist Recommended",
                "Action Plan Template"
            ]
            
            for section in required_sections:
                self.assertIn(section, content)
                
            print(f"✅ Module 5 content includes all required sections")
        except Exception as e:
            print(f"❌ Module 5 content test failed: {str(e)}")
            raise
    
    def test_04_module5_glossary_terms(self):
        """Test that the 5 new glossary terms for Module 5 exist"""
        try:
            required_terms = [
                "Tax Exposure",
                "Lever Hierarchy",
                "Personalized Planning",
                "Strategy Stack",
                "Advisor Integration"
            ]
            
            for term_name in required_terms:
                term = next((t for t in self.glossary_terms if t["term"] == term_name), None)
                self.assertIsNotNone(term, f"Glossary term '{term_name}' not found")
                
            print(f"✅ All 5 Module 5 glossary terms exist")
        except Exception as e:
            print(f"❌ Module 5 glossary terms test failed: {str(e)}")
            raise
    
    def test_05_module5_quiz_questions(self):
        """Test that Module 5 has 3 quiz questions with correct answers"""
        try:
            self.assertEqual(len(self.module5_quiz_questions), 3)
            
            # Expected questions and answers
            expected_qa = [
                {
                    "question": "What determines which levers apply to you?",
                    "answer": "Your income type, entity structure, and timing flexibility"
                },
                {
                    "question": "What's the purpose of building a glossary + case study reference set?",
                    "answer": "To help you align the right tools and strategies with your profile"
                },
                {
                    "question": "What is the goal of an Escape Plan?",
                    "answer": "To apply the tax code proactively and reduce lifetime tax burden"
                }
            ]
            
            for expected in expected_qa:
                question = next((q for q in self.module5_quiz_questions if q["question"] == expected["question"]), None)
                self.assertIsNotNone(question, f"Question '{expected['question']}' not found")
                self.assertEqual(question["correct_answer"], expected["answer"])
                
            print(f"✅ Module 5 has 3 quiz questions with correct answers")
        except Exception as e:
            print(f"❌ Module 5 quiz questions test failed: {str(e)}")
            raise
    
    def test_06_module5_xp_available(self):
        """Test that Module 5 shows 50 XP available"""
        try:
            # Calculate XP based on module index (5) * 10
            expected_xp = 5 * 10
            
            # Verify each quiz question is worth 10 points
            for question in self.module5_quiz_questions:
                self.assertEqual(question["points"], 10)
                
            # Total XP should be number of questions * points per question
            total_xp = len(self.module5_quiz_questions) * 10
            self.assertEqual(total_xp, expected_xp)
                
            print(f"✅ Module 5 has {expected_xp} XP available")
        except Exception as e:
            print(f"❌ Module 5 XP test failed: {str(e)}")
            raise
    
    def test_07_final_cta(self):
        """Test that the final CTA appears in Module 5 content"""
        try:
            content = self.module5["content"]
            
            # Check for final CTA elements
            cta_elements = [
                "You've built your foundation",
                "You've seen the levers",
                "unlock access to",
                "full IRS Escape Plan course tracks",
                "Let's move from course to command",
                "Your plan starts now"
            ]
            
            for element in cta_elements:
                self.assertIn(element, content)
                
            print(f"✅ Module 5 includes the final CTA")
        except Exception as e:
            print(f"❌ Module 5 final CTA test failed: {str(e)}")
            raise

def run_tests():
    """Run all tests and print a summary"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(Module5Test)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    print("\n=== MODULE 5 TEST SUMMARY ===")
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
        print("\n✅ All Module 5 tests passed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())
