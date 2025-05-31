from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class CourseType(str, Enum):
    PRIMER = "primer"
    W2 = "w2"
    BUSINESS = "business"

class QuizQuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SCENARIO = "scenario"

class ToolType(str, Enum):
    CALCULATOR = "calculator"
    FORM_GENERATOR = "form_generator"
    PLANNER = "planner"

# Data Models
class CourseContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    content: str
    video_url: Optional[str] = None
    duration_minutes: int
    order_index: int

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: CourseType
    title: str
    description: str
    thumbnail_url: str
    is_free: bool
    total_lessons: int
    estimated_hours: int
    lessons: List[CourseContent] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    type: QuizQuestionType
    options: List[str] = []
    correct_answer: str
    explanation: str
    points: int = 10
    course_id: str

class GlossaryTerm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    definition: str
    category: str
    related_terms: List[str] = []

class Tool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: ToolType
    icon: str
    is_free: bool
    config: Dict[str, Any] = {}

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    lesson_id: str
    completed: bool = False
    score: Optional[int] = None
    completed_at: Optional[datetime] = None

# Course endpoints
@api_router.get("/courses", response_model=List[Course])
async def get_courses():
    courses = await db.courses.find().to_list(1000)
    return [Course(**course) for course in courses]

@api_router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return Course(**course)

@api_router.get("/courses/{course_id}/lessons", response_model=List[CourseContent])
async def get_course_lessons(course_id: str):
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return [CourseContent(**lesson) for lesson in course.get("lessons", [])]

# Quiz endpoints
@api_router.get("/courses/{course_id}/quiz", response_model=List[QuizQuestion])
async def get_course_quiz(course_id: str):
    questions = await db.quiz_questions.find({"course_id": course_id}).to_list(1000)
    return [QuizQuestion(**q) for q in questions]

@api_router.post("/quiz/submit")
async def submit_quiz_answer(course_id: str, question_id: str, answer: str):
    question = await db.quiz_questions.find_one({"id": question_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = question["correct_answer"].lower() == answer.lower()
    points = question["points"] if is_correct else 0
    
    return {
        "correct": is_correct,
        "points": points,
        "explanation": question["explanation"]
    }

# Glossary endpoints
@api_router.get("/glossary", response_model=List[GlossaryTerm])
async def get_glossary():
    terms = await db.glossary.find().to_list(1000)
    return [GlossaryTerm(**term) for term in terms]

@api_router.get("/glossary/search")
async def search_glossary(q: str):
    terms = await db.glossary.find({
        "$or": [
            {"term": {"$regex": q, "$options": "i"}},
            {"definition": {"$regex": q, "$options": "i"}}
        ]
    }).to_list(100)
    return [GlossaryTerm(**term) for term in terms]

# Tools endpoints
@api_router.get("/tools", response_model=List[Tool])
async def get_tools():
    tools = await db.tools.find().to_list(1000)
    return [Tool(**tool) for tool in tools]

@api_router.get("/tools/{tool_id}", response_model=Tool)
async def get_tool(tool_id: str):
    tool = await db.tools.find_one({"id": tool_id})
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return Tool(**tool)

# User progress endpoints
@api_router.post("/progress")
async def update_progress(progress: UserProgress):
    existing = await db.user_progress.find_one({
        "user_id": progress.user_id,
        "course_id": progress.course_id,
        "lesson_id": progress.lesson_id
    })
    
    if existing:
        await db.user_progress.update_one(
            {"id": existing["id"]},
            {"$set": progress.dict()}
        )
    else:
        await db.user_progress.insert_one(progress.dict())
    
    return {"status": "success"}

@api_router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    progress = await db.user_progress.find({"user_id": user_id}).to_list(1000)
    return [UserProgress(**p) for p in progress]

# Initialize sample data
@api_router.post("/initialize-data")
async def initialize_sample_data():
    # Clear existing data
    await db.courses.delete_many({})
    await db.quiz_questions.delete_many({})
    await db.glossary.delete_many({})
    await db.tools.delete_many({})
    
    # Sample courses
    primer_course = Course(
        type=CourseType.PRIMER,
        title="The Escape Blueprint",
        description="Essential fundamentals to understand your tax situation and escape IRS problems",
        thumbnail_url="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400",
        is_free=True,
        total_lessons=5,
        estimated_hours=2,
        lessons=[
            CourseContent(
                title="Understanding Your Tax Burden",
                description="Learn the basics of tax liability and common IRS issues",
                content="This lesson covers the fundamental concepts of tax burden, including how taxes are calculated, common mistakes that lead to IRS problems, and the first steps to take when facing tax issues.",
                duration_minutes=25,
                order_index=1
            ),
            CourseContent(
                title="IRS Communication Basics",
                description="How to interpret and respond to IRS notices",
                content="Understanding IRS letters and notices is crucial. This lesson teaches you how to read IRS correspondence, identify urgent vs. routine notices, and respond appropriately.",
                duration_minutes=30,
                order_index=2
            ),
            CourseContent(
                title="Payment Options Overview",
                description="Explore different ways to resolve tax debt",
                content="The IRS offers several payment options including payment plans, offers in compromise, and currently not collectible status. Learn which option might work for your situation.",
                duration_minutes=35,
                order_index=3
            ),
            CourseContent(
                title="Professional Help: When and How",
                description="Understanding when to seek professional assistance",
                content="Some tax situations require professional help. Learn when to contact a tax professional, what credentials to look for, and how to work effectively with tax representatives.",
                duration_minutes=20,
                order_index=4
            ),
            CourseContent(
                title="Creating Your Action Plan",
                description="Develop a personalized strategy for your tax situation",
                content="Put everything together to create a step-by-step action plan tailored to your specific tax situation and goals.",
                duration_minutes=30,
                order_index=5
            )
        ]
    )
    
    w2_course = Course(
        type=CourseType.W2,
        title="W-2 Escape Plan",
        description="Advanced strategies for W-2 employees to minimize taxes and resolve IRS issues",
        thumbnail_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
        is_free=False,
        total_lessons=8,
        estimated_hours=4,
        lessons=[
            CourseContent(
                title="W-2 Employee Tax Basics",
                description="Understanding payroll taxes and withholdings",
                content="Deep dive into how payroll taxes work, understanding your pay stub, and optimizing your withholdings.",
                duration_minutes=40,
                order_index=1
            ),
            CourseContent(
                title="Maximizing Deductions",
                description="Employee-specific deductions and strategies",
                content="Learn about deductions available to W-2 employees, including unreimbursed business expenses, home office deductions for remote work, and more.",
                duration_minutes=45,
                order_index=2
            )
        ]
    )
    
    business_course = Course(
        type=CourseType.BUSINESS,
        title="Business Owner Tax Freedom",
        description="Comprehensive tax strategies for business owners and entrepreneurs",
        thumbnail_url="https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400",
        is_free=False,
        total_lessons=12,
        estimated_hours=6,
        lessons=[
            CourseContent(
                title="Business Structure Tax Implications",
                description="Choosing the right business structure for tax benefits",
                content="Compare sole proprietorship, LLC, S-Corp, and C-Corp structures and their tax implications.",
                duration_minutes=50,
                order_index=1
            ),
            CourseContent(
                title="Business Deduction Strategies",
                description="Maximizing legitimate business deductions",
                content="Learn about all available business deductions including equipment, travel, meals, and home office expenses.",
                duration_minutes=55,
                order_index=2
            )
        ]
    )
    
    # Insert courses
    await db.courses.insert_one(primer_course.dict())
    await db.courses.insert_one(w2_course.dict())
    await db.courses.insert_one(business_course.dict())
    
    # Sample quiz questions
    quiz_questions = [
        QuizQuestion(
            question="What is the first step when you receive an IRS notice?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Ignore it", "Read it carefully", "Call a lawyer immediately", "Throw it away"],
            correct_answer="Read it carefully",
            explanation="Always read IRS notices carefully to understand what action is required and any deadlines.",
            course_id=primer_course.id
        ),
        QuizQuestion(
            question="Payment plans with the IRS require a setup fee.",
            type=QuizQuestionType.TRUE_FALSE,
            options=["True", "False"],
            correct_answer="True",
            explanation="The IRS charges a setup fee for payment plans, though it may be reduced for low-income taxpayers.",
            course_id=primer_course.id
        )
    ]
    
    for question in quiz_questions:
        await db.quiz_questions.insert_one(question.dict())
    
    # Sample glossary terms
    glossary_terms = [
        GlossaryTerm(
            term="AGI",
            definition="Adjusted Gross Income - Your total income minus specific deductions allowed by the IRS",
            category="Tax Terms",
            related_terms=["Gross Income", "Deductions", "Tax Liability"]
        ),
        GlossaryTerm(
            term="Offer in Compromise",
            definition="An agreement with the IRS that settles your tax debt for less than the full amount you owe",
            category="IRS Programs",
            related_terms=["Payment Plan", "Currently Not Collectible", "Tax Debt"]
        ),
        GlossaryTerm(
            term="Currently Not Collectible",
            definition="IRS status that temporarily delays collection due to financial hardship",
            category="IRS Programs",
            related_terms=["Offer in Compromise", "Payment Plan", "Financial Hardship"]
        )
    ]
    
    for term in glossary_terms:
        await db.glossary.insert_one(term.dict())
    
    # Sample tools
    tools = [
        Tool(
            name="Tax Liability Calculator",
            description="Calculate your estimated tax liability based on income and deductions",
            type=ToolType.CALCULATOR,
            icon="calculator",
            is_free=True,
            config={"fields": ["income", "deductions", "filing_status"]}
        ),
        Tool(
            name="Payment Plan Estimator",
            description="Estimate monthly payments for IRS payment plans",
            type=ToolType.CALCULATOR,
            icon="credit-card",
            is_free=True,
            config={"fields": ["total_debt", "plan_length", "income"]}
        ),
        Tool(
            name="Offer in Compromise Qualifier",
            description="Determine if you might qualify for an Offer in Compromise",
            type=ToolType.FORM_GENERATOR,
            icon="file-text",
            is_free=False,
            config={"fields": ["assets", "income", "expenses", "debt_amount"]}
        )
    ]
    
    for tool in tools:
        await db.tools.insert_one(tool.dict())
    
    return {"status": "Sample data initialized successfully"}

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "IRS Escape Plan API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
