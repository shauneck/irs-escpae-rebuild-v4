import requests
import unittest
import json
import uuid
import os
import sys

# Use the public endpoint for testing
BACKEND_URL = "https://2509541f-404c-4ef1-acc6-ed11dcdd6898.preview.emergentagent.com"

class W2EscapePlanModuleTest(unittest.TestCase):
    """Test suite for the W-2 Escape Plan Module 1 API"""

    def setUp(self):
        """Initialize test data"""
        self.api_url = f"{BACKEND_URL}/api"
        self.test_user_id = str(uuid.uuid4())
        self.courses = []
        self.w2_course = None
        self.glossary_terms = []
        
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
            
            # Find the W-2 Escape Plan course
            self.w2_course = next((c for c in self.courses if c["type"] == "w2"), None)
            self.assertIsNotNone(self.w2_course, "W-2 Escape Plan course not found")
            self.assertEqual(self.w2_course["title"], "W-2 Escape Plan", "W-2 course has incorrect title")
            print(f"✅ Found W-2 Escape Plan course: {self.w2_course['title']}")
            
            # Verify W-2 course has the expected properties
            self.assertEqual(self.w2_course["total_lessons"], 8, "W-2 course should have 8 total lessons")
            self.assertEqual(self.w2_course["estimated_hours"], 4, "W-2 course should have 4 estimated hours")
            print(f"✅ Verified W-2 course has 8 total lessons and 4 estimated hours")
        except Exception as e:
            print(f"❌ Get courses test failed: {str(e)}")
            raise
    
    def test_03_get_w2_course_lessons(self):
        """Test getting lessons for the W-2 Escape Plan course"""
        if not self.w2_course:
            self.test_02_get_courses()
        
        try:
            course_id = self.w2_course["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}/lessons")
            self.assertEqual(response.status_code, 200)
            lessons = response.json()
            self.assertGreaterEqual(len(lessons), 1)
            print(f"✅ Retrieved {len(lessons)} lessons for W-2 Escape Plan course")
            
            # Verify Module 1 exists and has the correct properties
            module1 = next((l for l in lessons if l["order_index"] == 1), None)
            self.assertIsNotNone(module1, "Module 1 not found in W-2 course lessons")
            self.assertEqual(module1["title"], "The Real Problem with W-2 Income", "Module 1 has incorrect title")
            self.assertEqual(module1["description"], "Module 1 of 8 - W-2 Income Mapping - Understand the disadvantages of W-2 income and discover strategic alternatives", "Module 1 has incorrect description")
            self.assertEqual(module1["duration_minutes"], 45, "Module 1 should be 45 minutes")
            print(f"✅ Verified Module 1: '{module1['title']}' exists with correct properties")
            
            # Verify Module 1 content contains key sections
            content = module1["content"]
            key_sections = [
                "The W-2 Disadvantage",
                "W-2 Profile Mapping Exercise",
                "Case Study: Olivia",
                "Strategic Alternatives to W-2 Limitations",
                "The **Forward-Looking Planning** Approach",  # Updated to match actual content
                "Your W-2 Escape Framework"
            ]
            
            for section in key_sections:
                self.assertIn(section, content, f"Module 1 content missing section: {section}")
            
            print(f"✅ Verified Module 1 content contains all required sections")
            
            # Verify glossary terms are present in the content (case-insensitive)
            glossary_terms = {
                "W-2 Income": ["W-2 income", "W-2 Income"],
                "Effective Tax Rate": ["effective tax rate", "Effective Tax Rate"],
                "CPA vs Strategist": ["CPA vs Strategist", "CPA vs strategist"],
                "Forward-Looking Planning": ["forward-looking planning", "Forward-Looking Planning"]
            }
            
            for term, variations in glossary_terms.items():
                found = False
                for variation in variations:
                    if variation.lower() in content.lower():
                        found = True
                        break
                self.assertTrue(found, f"Module 1 content missing glossary term: {term}")
            
            print(f"✅ Verified Module 1 content contains all required glossary terms")
        except Exception as e:
            print(f"❌ Get W-2 course lessons test failed: {str(e)}")
            raise
    
    def test_04_get_w2_module1_quiz(self):
        """Test getting quiz questions for W-2 Escape Plan Module 1"""
        if not self.w2_course:
            self.test_02_get_courses()
        
        try:
            course_id = self.w2_course["id"]
            response = requests.get(f"{self.api_url}/courses/{course_id}/quiz", params={"module_id": 1})
            self.assertEqual(response.status_code, 200)
            questions = response.json()
            
            # Verify there are 3 quiz questions for Module 1
            self.assertEqual(len(questions), 3, f"Expected 3 quiz questions for Module 1, got {len(questions)}")
            print(f"✅ Retrieved {len(questions)} quiz questions for W-2 Module 1")
            
            # Verify each question has 50 XP value
            for question in questions:
                self.assertEqual(question["points"], 50, f"Quiz question should be worth 50 XP, got {question['points']}")
            
            print(f"✅ Verified all Module 1 quiz questions are worth 50 XP each")
            
            # Verify the specific questions exist
            expected_questions = [
                "What is the primary disadvantage of W-2 income compared to other income types?",
                "In Olivia's case study, what strategy helped her reduce her effective tax rate from 34% to 21%?",
                "What is the key difference between forward-looking planning and traditional CPA approaches for W-2 earners?"
            ]
            
            actual_questions = [q["question"] for q in questions]
            for expected in expected_questions:
                self.assertIn(expected, actual_questions, f"Expected quiz question not found: {expected}")
            
            print(f"✅ Verified all required quiz questions exist for Module 1")
            
            # Save a question for the quiz submission test
            self.quiz_question = questions[0]
        except Exception as e:
            print(f"❌ Get W-2 Module 1 quiz test failed: {str(e)}")
            raise
    
    def test_05_submit_w2_module1_quiz_answer(self):
        """Test submitting a quiz answer for W-2 Escape Plan Module 1"""
        if not hasattr(self, 'quiz_question'):
            self.test_04_get_w2_module1_quiz()
        
        try:
            if hasattr(self, 'quiz_question'):
                course_id = self.w2_course["id"]
                question_id = self.quiz_question["id"]
                correct_answer = self.quiz_question["correct_answer"]
                
                # Test with correct answer
                response = requests.post(
                    f"{self.api_url}/quiz/submit",
                    params={"course_id": course_id, "question_id": question_id, "answer": correct_answer}
                )
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertTrue(result["correct"])
                self.assertEqual(result["points"], 50, "Correct answer should award 50 XP")
                print(f"✅ Submitted correct quiz answer successfully, awarded {result['points']} XP")
                
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
                print(f"✅ Submitted incorrect quiz answer successfully, awarded 0 XP")
            else:
                print(f"⚠️ No quiz questions found, skipping test")
        except Exception as e:
            print(f"❌ Submit W-2 Module 1 quiz answer test failed: {str(e)}")
            raise
    
    def test_06_get_glossary(self):
        """Test getting glossary terms"""
        try:
            response = requests.get(f"{self.api_url}/glossary")
            self.assertEqual(response.status_code, 200)
            self.glossary_terms = response.json()
            self.assertGreaterEqual(len(self.glossary_terms), 1)
            print(f"✅ Retrieved {len(self.glossary_terms)} glossary terms")
            
            # Verify required glossary terms exist
            required_terms = ["W-2 Income", "Effective Tax Rate", "CPA vs Strategist", "Forward-Looking Planning"]
            term_names = [term["term"] for term in self.glossary_terms]
            
            for required_term in required_terms:
                self.assertIn(required_term, term_names, f"Required glossary term not found: {required_term}")
            
            print(f"✅ Verified all required glossary terms exist")
            
            # Save a term for the glossary XP test
            self.glossary_term = next((t for t in self.glossary_terms if t["term"] == "W-2 Income"), None)
        except Exception as e:
            print(f"❌ Get glossary test failed: {str(e)}")
            raise
    
    def test_07_award_glossary_xp(self):
        """Test awarding XP for viewing a glossary term"""
        if not hasattr(self, 'glossary_term'):
            self.test_06_get_glossary()
        
        try:
            if hasattr(self, 'glossary_term'):
                term_id = self.glossary_term["id"]
                
                # Create XP data
                xp_data = {
                    "user_id": self.test_user_id,
                    "term_id": term_id
                }
                
                response = requests.post(f"{self.api_url}/users/xp/glossary", json=xp_data)
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["xp_earned"], 5, "Glossary terms should award 5 XP")
                print(f"✅ Updated glossary XP successfully, awarded 5 XP")
            else:
                print("⚠️ No glossary terms found, skipping test")
        except Exception as e:
            print(f"❌ Update glossary XP test failed: {str(e)}")
            raise
    
    def test_08_award_quiz_xp(self):
        """Test awarding XP for completing a quiz question"""
        if not hasattr(self, 'quiz_question'):
            self.test_04_get_w2_module1_quiz()
        
        try:
            if hasattr(self, 'quiz_question'):
                course_id = self.w2_course["id"]
                question_id = self.quiz_question["id"]
                
                # Create XP data
                xp_data = {
                    "user_id": self.test_user_id,
                    "course_id": course_id,
                    "question_id": question_id,
                    "correct": True,
                    "points": 50  # Specify 50 points for W-2 course quiz
                }
                
                response = requests.post(f"{self.api_url}/users/xp/quiz", json=xp_data)
                self.assertEqual(response.status_code, 200)
                result = response.json()
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["xp_earned"], 50, "Quiz questions should award 50 XP")
                print(f"✅ Updated quiz XP successfully, awarded 50 XP")
            else:
                print(f"⚠️ No quiz questions found, skipping test")
        except Exception as e:
            print(f"❌ Update quiz XP test failed: {str(e)}")
            raise
    
    def test_09_get_user_xp(self):
        """Test getting user XP"""
        try:
            # First, submit a quiz answer and view a glossary term to earn some XP
            self.test_07_award_glossary_xp()
            self.test_08_award_quiz_xp()
            
            # Now get the user's XP
            response = requests.get(f"{self.api_url}/users/xp/{self.test_user_id}")
            self.assertEqual(response.status_code, 200)
            xp_data = response.json()
            
            # Verify XP structure
            required_fields = ["total_xp", "quiz_xp", "glossary_xp"]
            for field in required_fields:
                self.assertIn(field, xp_data)
            
            # Verify XP values
            self.assertGreaterEqual(xp_data["quiz_xp"], 50, "User should have at least 50 quiz XP")
            self.assertGreaterEqual(xp_data["glossary_xp"], 5, "User should have at least 5 glossary XP")
            self.assertGreaterEqual(xp_data["total_xp"], 55, "User should have at least 55 total XP")
            
            print(f"✅ Retrieved user XP: Total={xp_data['total_xp']}, Quiz={xp_data['quiz_xp']}, Glossary={xp_data['glossary_xp']}")
        except Exception as e:
            print(f"❌ Get user XP test failed: {str(e)}")
            raise

def run_tests():
    """Run all tests and print a summary"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(W2EscapePlanModuleTest)
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