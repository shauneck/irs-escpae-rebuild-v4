import requests
import unittest
import sys
from pprint import pprint

class W2EscapePlanModuleTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(W2EscapePlanModuleTest, self).__init__(*args, **kwargs)
        self.base_url = "https://5cae3060-20f9-4b8b-b436-5b7713b729a5.preview.emergentagent.com/api"
        self.w2_course_id = None
        self.module_3_id = None
        self.glossary_terms = []

    def setUp(self):
        # Get all courses to find the W-2 Escape Plan course
        response = requests.get(f"{self.base_url}/courses")
        self.assertEqual(response.status_code, 200, "Failed to fetch courses")
        
        courses = response.json()
        for course in courses:
            if course["title"] == "W-2 Escape Plan":
                self.w2_course_id = course["id"]
                break
        
        self.assertIsNotNone(self.w2_course_id, "W-2 Escape Plan course not found")
        
        # Get glossary terms
        response = requests.get(f"{self.base_url}/glossary")
        self.assertEqual(response.status_code, 200, "Failed to fetch glossary terms")
        self.glossary_terms = response.json()

    def test_w2_course_exists(self):
        """Test that the W-2 Escape Plan course exists"""
        response = requests.get(f"{self.base_url}/courses/{self.w2_course_id}")
        self.assertEqual(response.status_code, 200, "Failed to fetch W-2 course")
        
        course = response.json()
        self.assertEqual(course["title"], "W-2 Escape Plan", "Course title mismatch")
        self.assertEqual(course["type"], "w2", "Course type mismatch")
        self.assertEqual(len(course["lessons"]), 3, "Course should have 3 modules")
        
        # Verify Module 3 exists
        module_3 = None
        for lesson in course["lessons"]:
            if lesson["order_index"] == 3:
                module_3 = lesson
                self.module_3_id = lesson["id"]
                break
        
        self.assertIsNotNone(module_3, "Module 3 not found in W-2 course")
        self.assertEqual(module_3["title"], "Stacking Offsets — The Tax Strategy Most W-2 Earners Miss", "Module 3 title mismatch")
        self.assertEqual(module_3["description"], "Module 3 of 8 - Offset Layering", "Module 3 description mismatch")
        self.assertEqual(module_3["duration_minutes"], 55, "Module 3 duration mismatch")
        
        print("✅ W-2 Escape Plan course and Module 3 exist with correct metadata")

    def test_module_3_content(self):
        """Test that Module 3 content is complete and contains all required sections"""
        response = requests.get(f"{self.base_url}/courses/{self.w2_course_id}")
        self.assertEqual(response.status_code, 200, "Failed to fetch W-2 course")
        
        course = response.json()
        module_3 = None
        for lesson in course["lessons"]:
            if lesson["order_index"] == 3:
                module_3 = lesson
                break
        
        self.assertIsNotNone(module_3, "Module 3 not found in W-2 course")
        
        # Check for required sections in content
        required_sections = [
            "Understanding Offset Stacking",
            "Why Single-Strategy Approaches Fall Short",
            "Case Study: Helen",
            "Advanced Offset Stacking Strategies",
            "Building Your Deduction Portfolio",
            "Common Offset Stacking Mistakes to Avoid",
            "Measuring Offset Stacking Success",
            "Advanced Coordination Strategies",
            "What's Next: Entity Structure Optimization"
        ]
        
        for section in required_sections:
            self.assertIn(section, module_3["content"], f"Section '{section}' not found in Module 3 content")
        
        # Check for Helen case study details
        helen_case_study_details = [
            "Year 1 Recap: $156K STR depreciation success",
            "Year 2 Challenge: $220K W-2 + $150K bonus = $370K income",
            "3-Phase Strategy",
            "STR expansion",
            "Energy investments",
            "Equipment depreciation",
            "$443K total deductions",
            "$370K income",
            "$0 taxes",
            "$73K carryforward",
            "$2M+ assets",
            "$127K annual cash flow"
        ]
        
        for detail in helen_case_study_details:
            self.assertIn(detail, module_3["content"], f"Helen case study detail '{detail}' not found in Module 3 content")
        
        print("✅ Module 3 content contains all required sections and Helen case study details")

    def test_module_2_glossary_terms(self):
        """Test that required glossary terms for Module 2 exist"""
        required_terms = [
            "Repositioning",
            "Qualified Opportunity Fund",
            "Short-Term Rental",
            "Bonus Depreciation",
            "Material Participation",
            "Depreciation Loss",
            "Capital Gain Deferral"
        ]
        
        found_terms = []
        for term in self.glossary_terms:
            for required_term in required_terms:
                if required_term.lower() in term["term"].lower():
                    found_terms.append(required_term)
                    break
        
        for term in required_terms:
            self.assertIn(term, found_terms, f"Glossary term '{term}' not found")
        
        print("✅ All required glossary terms for Module 2 exist")

    def test_module_2_quiz(self):
        """Test that Module 2 quiz questions exist and have correct XP values"""
        response = requests.get(f"{self.base_url}/courses/{self.w2_course_id}/quiz?module_id=2")
        self.assertEqual(response.status_code, 200, "Failed to fetch Module 2 quiz questions")
        
        questions = response.json()
        self.assertEqual(len(questions), 3, "Module 2 should have 3 quiz questions")
        
        # Verify the specific questions
        expected_questions = [
            "What is the primary purpose of 'repositioning' already-taxed W-2 income?",
            "In Helen's case study, what was the key strategy that allowed her to eliminate her W-2 tax burden?",
            "What is the key requirement to use Short-Term Rental depreciation losses against W-2 income?"
        ]
        
        for question in questions:
            self.assertIn(question["question"], expected_questions, f"Unexpected quiz question: {question['question']}")
            self.assertEqual(question["points"], 50, f"Quiz question should be worth 50 XP: {question['question']}")
            self.assertEqual(question["module_id"], 2, f"Quiz question should be for module 2: {question['question']}")
        
        print("✅ Module 2 quiz has 3 questions worth 50 XP each (150 XP total)")

    def test_quiz_submission(self):
        """Test that quiz submission works and awards correct XP"""
        # Get quiz questions
        response = requests.get(f"{self.base_url}/courses/{self.w2_course_id}/quiz?module_id=2")
        self.assertEqual(response.status_code, 200, "Failed to fetch Module 2 quiz questions")
        
        questions = response.json()
        self.assertTrue(len(questions) > 0, "No quiz questions found")
        
        # Test submitting a correct answer
        question = questions[0]
        response = requests.post(
            f"{self.base_url}/quiz/submit?course_id={self.w2_course_id}&question_id={question['id']}&answer={question['correct_answer']}"
        )
        self.assertEqual(response.status_code, 200, "Failed to submit quiz answer")
        
        result = response.json()
        self.assertTrue(result["correct"], "Answer should be marked as correct")
        self.assertEqual(result["points"], 50, "Correct answer should award 50 XP")
        
        # Test submitting an incorrect answer
        wrong_answer = "Wrong answer"
        for option in question["options"]:
            if option != question["correct_answer"]:
                wrong_answer = option
                break
                
        response = requests.post(
            f"{self.base_url}/quiz/submit?course_id={self.w2_course_id}&question_id={question['id']}&answer={wrong_answer}"
        )
        self.assertEqual(response.status_code, 200, "Failed to submit quiz answer")
        
        result = response.json()
        self.assertFalse(result["correct"], "Answer should be marked as incorrect")
        self.assertEqual(result["points"], 0, "Incorrect answer should award 0 XP")
        
        print("✅ Quiz submission works correctly, awarding 50 XP for correct answers")

    def test_xp_tracking(self):
        """Test that XP tracking works for quiz and glossary terms"""
        # Get initial XP
        response = requests.get(f"{self.base_url}/users/xp")
        self.assertEqual(response.status_code, 200, "Failed to fetch user XP")
        
        initial_xp = response.json()["total_xp"]
        
        # Award glossary XP
        if len(self.glossary_terms) > 0:
            response = requests.post(
                f"{self.base_url}/users/xp/glossary",
                json={"term_id": self.glossary_terms[0]["id"]}
            )
            self.assertEqual(response.status_code, 200, "Failed to award glossary XP")
            
            # Verify XP increased
            response = requests.get(f"{self.base_url}/users/xp")
            self.assertEqual(response.status_code, 200, "Failed to fetch updated user XP")
            
            updated_xp = response.json()["total_xp"]
            self.assertEqual(updated_xp, initial_xp + 5, "Glossary term should award 5 XP")
        
        # Award quiz XP
        response = requests.post(
            f"{self.base_url}/users/xp/quiz",
            json={"points": 50}
        )
        self.assertEqual(response.status_code, 200, "Failed to award quiz XP")
        
        # Verify XP increased
        response = requests.get(f"{self.base_url}/users/xp")
        self.assertEqual(response.status_code, 200, "Failed to fetch updated user XP")
        
        final_xp = response.json()["total_xp"]
        self.assertEqual(final_xp, initial_xp + 5 + 50, "Total XP should increase by 55")
        
        print("✅ XP tracking works correctly for both quiz and glossary terms")

def run_tests():
    suite = unittest.TestSuite()
    suite.addTest(W2EscapePlanModuleTest('test_w2_course_exists'))
    suite.addTest(W2EscapePlanModuleTest('test_module_2_content'))
    suite.addTest(W2EscapePlanModuleTest('test_module_2_glossary_terms'))
    suite.addTest(W2EscapePlanModuleTest('test_module_2_quiz'))
    suite.addTest(W2EscapePlanModuleTest('test_quiz_submission'))
    suite.addTest(W2EscapePlanModuleTest('test_xp_tracking'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("🔍 Testing W-2 Escape Plan Module 2 API functionality...")
    success = run_tests()
    sys.exit(0 if success else 1)
