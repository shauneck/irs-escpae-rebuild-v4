#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv('/app/backend/.env')

# Read the new content
with open('/app/updated_module9_content.md', 'r') as f:
    new_content = f.read()

async def add_module9():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Create new Module 9 lesson
    new_lesson = {
        "id": str(uuid.uuid4()),
        "title": "The Exit Plan",
        "description": "Module 9 of 12 - Master the three-pillar exit strategy using QSBS, QOF, and installment planning to achieve zero capital gains tax on business exits",
        "content": new_content,
        "video_url": None,
        "duration_minutes": 100,
        "order_index": 9,
        "xp_available": 200  # Higher XP as this is the culmination module
    }
    
    # Add the new lesson to the course
    result = await db.courses.update_one(
        {"id": business_course_id},
        {
            "$push": {"lessons": new_lesson},
            "$inc": {"total_lessons": 1}
        }
    )
    
    if result.modified_count > 0:
        print("✅ Module 9 successfully added to the course!")
        print(f"Added lesson: {new_lesson['title']}")
        print(f"Lesson ID: {new_lesson['id']}")
        print(f"Duration: {new_lesson['duration_minutes']} minutes")
        print(f"XP Available: {new_lesson['xp_available']} (Culmination Module)")
    else:
        print("❌ Failed to add Module 9")
        print("Course might not be found")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module9())