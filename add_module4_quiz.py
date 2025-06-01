#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module4_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 4 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What's a key advantage of oil & gas investments under IRC §263?",
            "type": "multiple_choice",
            "options": [
                "They provide high deductions that can offset active income",
                "They create permanent passive losses", 
                "They defer capital gains into a future year",
                "They eliminate the need for cost segregation"
            ],
            "correct_answer": "They provide high deductions that can offset active income",
            "explanation": "Oil & gas investments under IRC §263 allow for immediate deduction of intangible drilling costs (IDC), typically 70-85% of the investment, which can offset active business income in the current year.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 4
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is the role of REPS in deduction stacking?",
            "type": "multiple_choice", 
            "options": [
                "It allows real estate losses to be used against active income",
                "It accelerates long-term capital gains",
                "It allows the MSO to deduct officer salaries", 
                "It reduces cost seg requirements"
            ],
            "correct_answer": "It allows real estate losses to be used against active income",
            "explanation": "Real Estate Professional Status (REPS) removes the passive loss limitations, allowing unlimited real estate depreciation and losses to be deducted against active business income.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 4
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What does a cost segregation study enable?",
            "type": "multiple_choice",
            "options": [
                "Accelerated depreciation of real estate components",
                "Deducting all property value in year one",
                "Avoiding 1031 exchange rules",
                "Capital loss carryforward to retirement"
            ],
            "correct_answer": "Accelerated depreciation of real estate components", 
            "explanation": "Cost segregation studies identify building components that can be depreciated over 5, 7, or 15 years instead of the standard 27.5/39 years, creating substantial first-year deductions through accelerated depreciation.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 4
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Why is structure critical to using these deductions effectively?",
            "type": "multiple_choice",
            "options": [
                "Because deductions must flow through the right entity to be fully usable",
                "Because the IRS audits trusts more than corporations",
                "Because cash balance plans limit real estate benefits", 
                "Because REPS only applies to LLCs"
            ],
            "correct_answer": "Because deductions must flow through the right entity to be fully usable",
            "explanation": "Proper entity structuring ensures deductions flow to the appropriate tax return and can be fully utilized. For example, MSO-funded investments need proper documentation, and REPS requires the right entity ownership structure.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 4
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 4!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module4_quiz())