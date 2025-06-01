#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module5_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 5 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What is the main tax benefit of QSBS under IRC §1202?",
            "type": "multiple_choice",
            "options": [
                "Up to $10M in capital gains exclusion after 5 years",
                "Unlimited ordinary income deductions",
                "Deferral of all business income for 10 years", 
                "Conversion of ordinary income to capital gains"
            ],
            "correct_answer": "Up to $10M in capital gains exclusion after 5 years",
            "explanation": "Qualified Small Business Stock (QSBS) under IRC §1202 provides up to $10 million (or 10x basis) in tax-free capital gains exclusion per person after holding the stock for at least 5 years.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 5
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What does a QOF allow you to do?",
            "type": "multiple_choice",
            "options": [
                "Defer gains and earn tax-free growth on new appreciation",
                "Convert capital gains to ordinary income",
                "Eliminate depreciation recapture permanently",
                "Deduct investment losses against ordinary income"
            ],
            "correct_answer": "Defer gains and earn tax-free growth on new appreciation",
            "explanation": "Qualified Opportunity Funds (QOF) allow investors to defer capital gains until 2026 and, after a 10-year hold, receive all new appreciation completely tax-free.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 5
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Why would a business owner use an installment sale?",
            "type": "multiple_choice",
            "options": [
                "To smooth income over multiple years and reduce tax spikes",
                "To convert capital gains into ordinary income",
                "To qualify for QSBS treatment",
                "To avoid state income taxes permanently"
            ],
            "correct_answer": "To smooth income over multiple years and reduce tax spikes",
            "explanation": "Installment sales spread gain recognition over multiple years, which can keep the seller in lower tax brackets and avoid large tax spikes from recognizing all gains in a single year.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 5
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is the role of F-reorg in exit planning?",
            "type": "multiple_choice",
            "options": [
                "It allows S-Corp owners to convert to a C-Corp without triggering tax",
                "It eliminates all capital gains on business sales",
                "It creates unlimited QSBS benefits regardless of holding period",
                "It converts business assets to personal assets tax-free"
            ],
            "correct_answer": "It allows S-Corp owners to convert to a C-Corp without triggering tax",
            "explanation": "An F-reorganization under IRC §368 allows S-Corporation owners to convert to C-Corporation status without triggering immediate tax, enabling them to start the 5-year QSBS holding period clock.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 5
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 5!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module5_quiz())