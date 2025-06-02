#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module9_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 9 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What's the capital gains exclusion under QSBS?",
            "type": "multiple_choice",
            "options": [
                "Up to $10M per trust or 10x basis, multiplied across trusts",
                "Up to $5M per person with no multiplication",
                "Up to $1M per year for 10 years",
                "Unlimited exclusion for any C-Corporation"
            ],
            "correct_answer": "Up to $10M per trust or 10x basis, multiplied across trusts",
            "explanation": "QSBS under IRC §1202 provides up to $10 million (or 10x basis) tax-free capital gains exclusion per person or trust, which can be multiplied across multiple trusts for substantial tax-free gains.",
            "points": 15,
            "course_id": business_course_id,
            "module_id": 9
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is the purpose of a QOF?",
            "type": "multiple_choice",
            "options": [
                "To defer capital gains and earn tax-free upside",
                "To eliminate all business taxes permanently",
                "To convert ordinary income to capital gains",
                "To provide unlimited depreciation deductions"
            ],
            "correct_answer": "To defer capital gains and earn tax-free upside",
            "explanation": "Qualified Opportunity Funds (QOF) allow investors to defer capital gains until 2026/2027 and, after a 10-year hold, receive all new appreciation completely tax-free.",
            "points": 15,
            "course_id": business_course_id,
            "module_id": 9
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Why use an installment sale for part of an exit?",
            "type": "multiple_choice",
            "options": [
                "To smooth income over time and reduce tax spikes",
                "To avoid all capital gains taxes permanently",
                "To qualify for QSBS treatment automatically",
                "To eliminate the need for professional advisors"
            ],
            "correct_answer": "To smooth income over time and reduce tax spikes",
            "explanation": "Installment sales spread gain recognition over multiple years, helping to keep sellers in lower tax brackets and avoid large tax spikes from recognizing all gains in a single year.",
            "points": 15,
            "course_id": business_course_id,
            "module_id": 9
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What does an F-reorg allow you to do?",
            "type": "multiple_choice",
            "options": [
                "Convert an S-Corp into a QSBS-qualified C-Corp without triggering tax",
                "Eliminate all future tax obligations",
                "Convert business assets to personal assets tax-free",
                "Qualify for unlimited depreciation deductions"
            ],
            "correct_answer": "Convert an S-Corp into a QSBS-qualified C-Corp without triggering tax",
            "explanation": "An F-reorganization under IRC §368 allows S-Corporation owners to convert to C-Corporation status without triggering immediate tax, enabling them to start the 5-year QSBS holding period for future tax-free gains.",
            "points": 15,
            "course_id": business_course_id,
            "module_id": 9
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 9!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
        print(f"     Points: {question['points']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module9_quiz())