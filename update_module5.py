#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Read the new content
with open('/app/updated_module5_content.md', 'r') as f:
    new_content = f.read()

async def update_lesson():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Course ID and lesson ID for Module 5
    course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    lesson_id = "ca0e8d5a-b26c-40e5-b5c4-9f5049d0d273"
    
    # Update the specific lesson content and metadata
    result = await db.courses.update_one(
        {
            "id": course_id,
            "lessons.id": lesson_id
        },
        {
            "$set": {
                "lessons.$.content": new_content,
                "lessons.$.title": "Capital Gains Repositioning & Strategic Exit",
                "lessons.$.description": "Module 5 of 12 - Master QSBS, QOF, and installment strategies to minimize capital gains and optimize business exits",
                "lessons.$.duration_minutes": 75
            }
        }
    )
    
    if result.modified_count > 0:
        print("✅ Module 5 content successfully updated!")
        print(f"Modified {result.modified_count} document(s)")
        print("Updated: Title, Description, Duration, and Content")
    else:
        print("❌ No documents were modified")
        print("This could mean the course or lesson ID was not found")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(update_lesson())