#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

async def add_module8_quiz():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Module 8 Quiz Questions
    quiz_questions = [
        {
            "id": str(uuid.uuid4()),
            "question": "What's the goal of the Wealth Multiplier Loop?",
            "type": "multiple_choice",
            "options": [
                "Create a self-funding system where tax savings generate assets and recurring income",
                "Maximize deductions in a single year only",
                "Avoid all investment risks permanently",
                "Eliminate the need for professional advisors"
            ],
            "correct_answer": "Create a self-funding system where tax savings generate assets and recurring income",
            "explanation": "The Wealth Multiplier Loop creates a self-sustaining system where tax savings fund asset acquisition, which generates income that funds additional tax strategies, creating perpetual wealth compounding.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 8
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What role does the MSO play in the loop?",
            "type": "multiple_choice",
            "options": [
                "It funds each layer — from investments to premiums — off the 1040",
                "It only handles payroll and compliance",
                "It replaces the need for personal tax planning",
                "It eliminates all business risks automatically"
            ],
            "correct_answer": "It funds each layer — from investments to premiums — off the 1040",
            "explanation": "The MSO serves as the coordination center for the wealth loop, funding investments, split-dollar premiums, and strategic acquisitions while providing professional management and tax optimization.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 8
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is the benefit of reinvesting tax savings?",
            "type": "multiple_choice",
            "options": [
                "You generate more deductions and more income in the next year",
                "You avoid all future tax obligations permanently",
                "You eliminate the need for additional planning",
                "You guarantee investment returns"
            ],
            "correct_answer": "You generate more deductions and more income in the next year",
            "explanation": "Reinvesting tax savings into income-producing assets creates a compounding effect where each investment generates both ongoing income and additional tax deductions for future years.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 8
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What does this loop replace?",
            "type": "multiple_choice",
            "options": [
                "One-off deductions that don't scale",
                "All business operations entirely",
                "The need for income generation",
                "Professional tax preparation"
            ],
            "correct_answer": "One-off deductions that don't scale",
            "explanation": "The Wealth Multiplier Loop replaces traditional one-time tax strategies with a systematic, compounding approach that scales and becomes self-sustaining over time.",
            "points": 10,
            "course_id": business_course_id,
            "module_id": 8
        }
    ]
    
    # Insert quiz questions
    result = await db.quiz_questions.insert_many(quiz_questions)
    
    print(f"✅ Successfully added {len(result.inserted_ids)} quiz questions for Module 8!")
    print("Quiz questions added:")
    for i, question in enumerate(quiz_questions, 1):
        print(f"  {i}. {question['question']}")
        print(f"     ✅ {question['correct_answer']}")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module8_quiz())