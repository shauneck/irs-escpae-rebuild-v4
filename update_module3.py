#!/usr/bin/env python3

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Read the new content
with open('/app/updated_module3_content.md', 'r') as f:
    new_content = f.read()

async def update_lesson():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Course ID and lesson ID
    course_id = "655aecd9-8cbc-48b4-9fe2-ea87765e0d68"
    lesson_id = "1130506e-327b-4c23-bf7b-a72062ac6e3f"
    
    # Update the specific lesson content
    result = await db.courses.update_one(
        {
            "id": course_id,
            "lessons.id": lesson_id
        },
        {
            "$set": {
                "lessons.$.content": new_content
            }
        }
    )
    
    if result.modified_count > 0:
        print("✅ Module 3 content successfully updated!")
        print(f"Modified {result.modified_count} document(s)")
    else:
        print("❌ No documents were modified")
        print("This could mean the course or lesson ID was not found")
    
    # Close the database connection
    client.close()

if __name__ == "__main__":
    asyncio.run(update_lesson())