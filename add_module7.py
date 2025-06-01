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
with open('/app/updated_module7_content.md', 'r') as f:
    new_content = f.read()

async def add_module7():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Business Owner course ID
    business_course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    
    # Create new Module 7 lesson
    new_lesson = {
        "id": str(uuid.uuid4()),
        "title": "How to Earn Income and Pay Zero Tax",
        "description": "Module 7 of 12 - Master the five-pillar zero-tax system using oil & gas, REPS, bonus depreciation, and split-dollar strategies to eliminate federal tax liability",
        "content": new_content,
        "video_url": None,
        "duration_minutes": 90,
        "order_index": 7,
        "xp_available": 150
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
        print("✅ Module 7 successfully added to the course!")
        print(f"Added lesson: {new_lesson['title']}")
        print(f"Lesson ID: {new_lesson['id']}")
        print(f"Duration: {new_lesson['duration_minutes']} minutes")
    else:
        print("❌ Failed to add Module 7")
        print("Course might not be found")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_module7())