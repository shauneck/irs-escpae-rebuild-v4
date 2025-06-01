#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module7_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 7 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What's the deduction range for oil & gas under IRC §263?",
            "type": "multiple_choice",
            "options": [
                "75–90% of the investment amount",
                "50–65% of the investment amount",
                "100% in the year of sale only",
                "25–40% spread over 10 years"
            ],
            "correct_answer": "75–90% of the investment amount",
            "explanation": "Oil & gas investments under IRC §263 allow for immediate deduction of intangible drilling costs (IDC), typically providing 75-90% of the investment amount as an immediate deduction against active income.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 7
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Why does REPS matter in this strategy?",
            "type": "multiple_choice",
            "options": [
                "It allows rental losses to offset active income",
                "It provides additional business deductions",
                "It reduces the cost of real estate purchases",
                "It eliminates the need for depreciation schedules"
            ],
            "correct_answer": "It allows rental losses to offset active income",
            "explanation": "Real Estate Professional Status (REPS) removes passive loss limitations, allowing unlimited real estate depreciation and losses to be deducted against active business income, which is crucial for the zero-tax strategy.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 7
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What's a benefit of acquiring depreciable business assets?",
            "type": "multiple_choice",
            "options": [
                "You can deduct a portion of the purchase via bonus depreciation",
                "The business becomes completely tax-free",
                "All expenses become deductible immediately",
                "It automatically qualifies for QSBS treatment"
            ],
            "correct_answer": "You can deduct a portion of the purchase via bonus depreciation",
            "explanation": "Strategic acquisition of businesses with depreciable assets allows for immediate deduction of a substantial portion of the purchase price through bonus depreciation, creating significant first-year tax benefits.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 7
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What does the split-dollar strategy accomplish?",
            "type": "multiple_choice",
            "options": [
                "Allows tax-free extraction of capital from an MSO",
                "Doubles all business deductions automatically",
                "Eliminates the need for business insurance",
                "Creates unlimited passive loss deductions"
            ],
            "correct_answer": "Allows tax-free extraction of capital from an MSO",
            "explanation": "Split-dollar life insurance strategies allow tax-free extraction of MSO capital through loan arrangements to fund life insurance policies in trusts, providing tax-free growth and estate planning benefits.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 7
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 7!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module7_quiz())