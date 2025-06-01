#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module6_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 6 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What is the purpose of using a trust alongside an MSO?",
            "type": "multiple_choice",
            "options": [
                "To remove assets from the estate and protect against liability",
                "To increase the MSO's tax deductions",
                "To qualify for QSBS treatment automatically",
                "To avoid all corporate compliance requirements"
            ],
            "correct_answer": "To remove assets from the estate and protect against liability",
            "explanation": "Irrevocable trusts work alongside MSOs to provide asset protection from personal creditors and remove assets from the owner's taxable estate, while the MSO handles income shifting and operational protection.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 6
        },
        {
            "id": str(uuid.uuid4()),
            "question": "How are split-dollar policies typically funded in this structure?",
            "type": "multiple_choice",
            "options": [
                "The MSO loans premiums to the trust",
                "The business owner pays premiums directly",
                "The trust borrows from external banks",
                "Premiums are paid with after-tax personal income"
            ],
            "correct_answer": "The MSO loans premiums to the trust",
            "explanation": "In a split-dollar arrangement, the MSO loans premium payments directly to the trust, which owns the life insurance policy. This creates tax-efficient funding while maintaining proper ownership and protection structures.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 6
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What allows the business owner to retain control?",
            "type": "multiple_choice",
            "options": [
                "Board control and trust powers",
                "Direct ownership of all entities",
                "Personal guarantees on all investments",
                "Keeping everything in their individual name"
            ],
            "correct_answer": "Board control and trust powers",
            "explanation": "Business owners maintain practical control through board representation in the MSO and advisory powers in the trust structure, allowing them to direct strategy and decisions without direct legal ownership.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 6
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What's a key benefit of co-investing through the MSO and trust?",
            "type": "multiple_choice",
            "options": [
                "Deductions and cash flow without personal exposure",
                "Elimination of all investment risks",
                "Guaranteed returns on all investments",
                "Ability to deduct personal living expenses"
            ],
            "correct_answer": "Deductions and cash flow without personal exposure",
            "explanation": "Co-investing through MSO and trust structures provides tax deductions for the MSO, protected cash flow growth in the trust, and shields the business owner from personal liability exposure on the investments.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 6
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 6!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module6_quiz())