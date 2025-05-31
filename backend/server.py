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
    module_id: int = 1  # Which module this question belongs to

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
@api_router.get("/courses/{course_id}/quiz")
async def get_course_quiz(course_id: str, module_id: int = None):
    if module_id:
        questions = await db.quiz_questions.find({"course_id": course_id, "module_id": module_id}).to_list(1000)
    else:
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
        total_lessons=9,
        estimated_hours=2,
        lessons=[
            CourseContent(
                title="Why You're Overpaying the IRS (and What to Do About It)",
                description="Module 1 of 5 - Discover why the tax code rewards wealth-building behavior and how strategists differ from traditional CPAs",
                content="""The U.S. **tax code** is not a punishment — it's a blueprint for **wealth-building behavior**. It rewards investment, ownership, and risk — and penalizes passive employment without structure.

Most **CPAs** file and reconcile. **Strategists** build infrastructure and optimize. High-income earners without proactive planning are the IRS's favorite clients.

## Core Concepts:

1. **The IRS is not your enemy — your ignorance is**
   The tax system is designed with clear rules and incentives. When you understand these rules, you can work within them to your advantage.

2. **CPAs file. Strategists plan.**
   Traditional CPAs focus on compliance and filing returns. **Tax strategists** focus on proactive planning to minimize future tax liability.

3. **There are only two outcomes in tax: proactive and overpaying**
   You either take control of your tax situation through strategic planning, or you accept whatever the default tax treatment gives you.

## Key Takeaways:

- The tax code rewards investment, business ownership, and calculated risk-taking
- Passive **W-2 income** without additional structure is taxed at the highest rates
- Strategic **tax planning** requires shifting from reactive filing to proactive structuring
- High-income earners without strategy consistently overpay taxes

## What's Next:

Filing saves nothing. Planning changes everything. Now that you've seen why most high-income earners overpay, let's look at the 6 Levers of Tax Control that shift the entire outcome.""",
                duration_minutes=25,
                order_index=1
            ),
            CourseContent(
                title="The 6 Levers That Actually Shift Your Tax Outcome",
                description="Module 2 of 5 - Master the fundamental levers that control all tax outcomes and strategies",
                content="""You don't need 600 tax strategies. You need 6 levers — the ones that actually move the needle. Every dollar you keep starts with one or more of these.

Most people think taxes are about forms. They're not — they're about structure, timing, and positioning. In this module, you'll learn the six foundational levers that every high-income strategy is built around:

## The 6 Core Levers

### 1. **Entity Type**
• Your **entity structure** determines your tax ceiling.
• C-Corp, S-Corp, MSO, or Schedule C — they're not all created equal.
• Strategically managing entity types is how business owners avoid double taxation and unlock deduction control.

### 2. **Income Type**
• Not all income is taxed equally.
• W-2, 1099, K-1, capital gains, passive flow — each has a different tax treatment.
• You don't need to earn less. You need to earn differently.

### 3. **Timing**
• Tax **timing** is a weapon — not a constraint.
• Installment sales, deferred comp, Roth conversions, **asset rollovers** all leverage when income hits.

### 4. **Asset Location**
• Where your assets live changes how they're taxed.
• Insurance wrappers, retirement accounts, real estate, and Opportunity Zones all have unique benefits.

### 5. **Deduction Strategy**
• Most CPAs miss over 50% of the **deductions** available.
• True planning involves orchestrating deductions through energy, depreciation, trust layering, and timing.

### 6. **Exit Planning**
• If you build wealth but don't plan your exit, the IRS cashes out with you.
• QSBS, Opportunity Zones, charitable trusts, and stepped-up basis strategy all come into play here.

## Application

These levers apply to:
• ✅ **Business owners** shifting to MSO or C-Corp models
• ✅ **W-2 earners** creating deduction pathways using asset placement
• ✅ **Real estate professionals** leveraging depreciation
• ✅ **Exit events** (business sale, asset sale, vesting RSUs)

Each future module in this course — and in the full IRS Escape Plan platform — ties back to one or more of these 6 levers.

## Moving Forward

You now have the lens. Every tax strategy moving forward pulls on one or more of these levers. In the next module, we'll walk through real-world case studies — showing exactly how W-2 earners and business owners legally reposition their income, time their exits, and keep hundreds of thousands more. Let's get tactical.""",
                duration_minutes=35,
                order_index=2
            ),
            CourseContent(
                title="Real Tax Case Studies That Shift Everything",
                description="Module 3 of 5 - See how real people used the 6 levers to keep six figures more through strategic tax planning",
                content="""You've seen the levers — now see what happens when real people pull them. These are not theoretical savings. These are real shifts from W-2 earners and business owners who rewired their tax exposure and kept six figures more.

This module walks through anonymized client **case studies** that reflect exactly how the 6 levers are used in real scenarios. These examples will show you how a shift in entity, income type, deduction strategy, or timing can result in transformational tax savings.

## Case Study 1 – W-2 Earner With RSUs

**Client:** "Noah" (Tech Executive)
**Income:** $550K W-2 + $380K **capital gains** from RSUs

**Levers Pulled:**
• Capital gains deferred using a **Qualified Opportunity Fund (QOF)**
• Basis invested in **STR** real estate for depreciation
• Net W-2 tax liability reduced by $96K

**Key Insight:** Capital gains don't need to be cashed out — they can be repositioned for long-term tax-free growth while offsetting current W-2 tax.

**The Strategy:**
Noah was facing a massive tax bill from his RSU vesting. Instead of paying capital gains tax immediately, he invested the proceeds into a Qualified Opportunity Fund, deferring the gains. The QOF investment went into short-term rental properties, generating depreciation that offset his W-2 income. Result: $96K tax savings in year one, with the potential for tax-free growth over 10+ years.

## Case Study 2 – Business Owner S-Corp Rollover

**Client:** "Jessica" (Agency Owner)
**Income:** $720K net income via S-Corp

**Levers Pulled:**
• Management fee routed to C-Corp MSO (Management Services Organization)
• **Retained earnings** invested into Oil & Gas and equipment **bonus depreciation**
• Effective tax liability dropped from $278K → $122K

**Key Insight:** Entity structure and asset pairing can transform the taxation of earned income and convert retained earnings into deduction-fueled passive cash flow.

**The Strategy:**
Jessica's agency was generating substantial profits as an S-Corp, but she was paying high personal tax rates on all the income. By creating a C-Corp MSO structure, she could retain earnings at lower corporate rates and invest them in bonus depreciation assets (oil & gas, equipment). This strategy saved her $156K in taxes while building long-term wealth through appreciating assets.

## Case Study 3 – W-2 + Real Estate

**Client:** "Liam" (Medical Professional)
**Income:** $400K W-2 + $120K net from STR (Virginia)

**Levers Pulled:**
• Qualified as **Real Estate Professional (REPS)** via material participation
• STR **depreciation offset** $118K of W-2 income
• Rental income reinvested into index fund via DCA

**Key Insight:** You don't need a business to get proactive. Real estate and depreciation rules can transform how income is taxed — even if you have a W-2 job.

**The Strategy:**
Liam was earning high W-2 income as a medical professional but wanted to reduce his tax burden. By qualifying for Real Estate Professional Status through material participation in his short-term rental properties, he could use the depreciation from his STR portfolio to offset his W-2 income. This strategy eliminated nearly $118K of taxable income while building a growing real estate portfolio.

## Key Takeaways from the Case Studies:

1. **Multiple Lever Approach:** Each case study shows how combining multiple levers creates exponential results
2. **Income Type Conversion:** Converting high-tax W-2 income into lower-tax investment income
3. **Timing Optimization:** Strategic deferral and acceleration of income and deductions
4. **Entity Leverage:** Using the right business structures to access better tax treatment
5. **Asset Positioning:** Placing the right investments in the right structures for maximum benefit

## The Common Thread:

These aren't loopholes. They're strategies — structured, code-backed, and available to anyone who stops playing defense. Each strategy follows the tax code exactly as written, using the incentives Congress built into the system to encourage investment, business ownership, and economic growth.

The difference between these clients and most high earners isn't access to secret strategies — it's the knowledge of how to structure their financial lives to take advantage of the opportunities already available.""",
                duration_minutes=45,
                order_index=3
            ),
            CourseContent(
                title="Mapping Your Tax Exposure",
                description="Module 4 of 5 - Guide yourself through self-assessment of income, entity structure, deduction strategy, and potential risk exposure",
                content="""Now that you understand the levers and have seen them in action, it's time to map your own **tax exposure**. This module will guide you through a systematic self-assessment of your current situation and help you identify which levers apply to your specific circumstances.

## Your Tax Exposure Assessment

Understanding your tax exposure requires analyzing four key areas:

### 1. Income Analysis - Your **AGI** Foundation

**Current Income Sources:**
• What types of income do you currently receive? (W-2, 1099, K-1, capital gains, rental, etc.)
• How much control do you have over the timing of this income?
• Are you maximizing or minimizing the AGI that determines your tax bracket?

**Income Type Stack Assessment:**
Your **Income Type Stack** determines not just how much you pay, but when you pay it. W-2 income hits immediately with limited deferral options, while business income offers significantly more control. Understanding your AGI composition is crucial for optimization.

### 2. Entity Structure Review - Your **Entity Exposure**

**Current Structure:**
• Are you operating as a sole proprietor, LLC, S-Corp, or C-Corp?
• Is your current entity structure optimized for your income level and business activities?
• What is your Entity Exposure - how much risk are you taking by not optimizing your structure?

**Optimization Opportunities:**
Different entity types offer different advantages. Higher-income individuals often benefit from more sophisticated structures that provide better tax treatment and asset protection. Reducing your Entity Exposure should be a priority for growing businesses.

### 3. Deduction Strategy Analysis - Your **Deduction Bandwidth**

**Current Deductions:**
• Are you maximizing standard vs. itemized deductions?
• What business deductions are you currently claiming?
• How much Deduction Bandwidth do you have - the gap between what you're claiming and what you could legally claim?

**Missed Opportunities:**
Most high earners leave significant deductions on the table because they don't have the right structures in place to capture them. Expanding your Deduction Bandwidth often requires proactive planning and proper documentation.

### 4. Risk Exposure Mapping

**Tax Risk Assessment:**
• How vulnerable are you to tax rate increases?
• Are you overly dependent on one income type?
• Do you have strategies in place for major income events (bonuses, stock vesting, business sales)?

**Future Planning:**
• What major income or life events are coming up?
• How will your current structure handle increased income?
• What's your exit strategy for current investments and business interests?

## Self-Assessment Framework

**Step 1: Document Your Current State**
• List all income sources and their tax treatment
• Identify your current entity structure and its limitations
• Calculate your effective tax rate and compare to optimal scenarios

**Step 2: Identify Your Biggest Opportunities**
• Which of the 6 levers offers the most immediate impact?
• What's your highest-value, lowest-risk optimization?
• Where are you leaving the most money on the table?

**Step 3: Prioritize Your Action Items**
• What can be implemented before year-end?
• What requires longer-term planning and structure changes?
• What professional help do you need to execute properly?

## Common Exposure Patterns

**High-Income W-2 Earners:**
• Typically over-exposed to ordinary income tax rates
• Limited deduction opportunities without additional structures
• Often missing real estate or business deduction strategies

**Business Owners:**
• May be using suboptimal entity structures for their income level
• Often missing advanced deduction and timing strategies
• Frequently lack proper exit planning for their business assets

**Investors and High-Net-Worth Individuals:**
• May have poor asset location strategies
• Often missing Opportunity Zone and other advanced deferral strategies
• Frequently lack coordination between different advisors and strategies

## Your Next Steps

The goal isn't to implement every strategy - it's to identify the 2-3 levers that will have the biggest impact on your specific situation and create a plan to implement them systematically.

In the final module, you'll learn how to build your personalized roadmap using the tools, glossary terms, and playbooks in your account. You're almost there.""",
                duration_minutes=40,
                order_index=4
            ),
            CourseContent(
                title="Building Your Custom Escape Plan",
                description="Module 5 of 5 - Create your personalized tax escape plan using the 6 levers, case studies, and strategic framework",
                content="""You've built your foundation. You've seen the levers. You've reviewed real case studies. And now — it's time to draft your own escape framework.

This module guides you through building your **personalized planning** approach based on your unique situation and the knowledge you've gained throughout this course.

## Your Profile Assessment

Understanding your profile type determines which strategies will have the biggest impact on your **tax exposure**:

### Profile Type Identification

**W-2 Dominant (70%+ W-2 income):**
• Primary focus: Deduction strategies and asset location
• Secondary opportunities: Real estate depreciation and timing
• Long-term goal: Building business income streams

**Business Owner (50%+ business income):**
• Primary focus: Entity optimization and exit planning
• Secondary opportunities: Timing and asset location
• Long-term goal: Scaling and succession planning

**Investor/Hybrid (Multiple income streams):**
• Primary focus: Asset location and timing arbitrage
• Secondary opportunities: Entity structures for investment activities
• Long-term goal: Coordinated wealth management

## Building Your **Lever Hierarchy**

Not all levers are equally valuable for your situation. Your **Lever Hierarchy** prioritizes where to focus first:

### High-Impact Levers (Start Here)
**For W-2 Earners:**
1. **Deduction Strategy** - Maximize available deductions
2. **Asset Location** - Optimize account placement
3. **Timing** - Control when income hits

**For Business Owners:**
1. **Entity Type** - Optimize business structure
2. **Exit Planning** - Plan for business growth and sale
3. **Deduction Strategy** - Maximize business deductions

**For Investors:**
1. **Asset Location** - Strategic account management
2. **Timing** - Harvest losses and control recognition
3. **Income Type** - Convert ordinary income to capital gains

### Your **Strategy Stack**

Your **Strategy Stack** combines multiple approaches for maximum impact:

**Foundation Layer:**
• Optimize current entity structure
• Maximize available deductions
• Implement proper asset location

**Growth Layer:**
• Add income diversification strategies
• Implement timing optimization
• Build depreciation assets

**Advanced Layer:**
• Sophisticated exit planning
• Multi-entity strategies
• Advanced timing arbitrage

## Mapping Your Resources

### Case Study Alignment
Review the case studies from Module 3 and identify which scenarios align with your profile:
• **Noah's QOF Strategy** - Best for high W-2 + capital gains
• **Jessica's Entity Optimization** - Best for profitable S-Corps
• **Liam's Real Estate Strategy** - Best for W-2 + real estate opportunities

### Tool Integration
From your assessment in Module 4, prioritize which tools and calculators will serve your specific situation:
• Tax liability calculators for scenario planning
• Payment plan estimators if dealing with current issues
• Deduction bandwidth analysis for optimization opportunities

## Implementation Timeline

### Year 1 (Foundation)
• Implement high-impact, low-complexity strategies
• Optimize current entity structure if needed
• Maximize available deductions
• Set up proper asset location

### Year 2-3 (Growth)
• Add income diversification strategies
• Implement depreciation assets if applicable
• Optimize timing of major income events
• Build relationships with specialists

### Year 3+ (Advanced)
• Implement sophisticated exit planning
• Consider multi-entity strategies
• Optimize for long-term wealth transfer
• Regular strategy reviews and updates

## **Advisor Integration**

Knowing when and how to work with tax strategists vs. traditional CPAs:

**DIY Appropriate:**
• Basic deduction optimization
• Simple asset location strategies
• Standard timing decisions

**Strategist Recommended:**
• Complex entity restructuring
• Multi-state tax planning
• Significant income events (business sale, large bonuses)
• Advanced depreciation strategies

**Team Approach:**
• CPA for compliance and filing
• Strategist for proactive planning
• Attorney for complex structures
• Financial advisor for investment coordination

## Your Action Plan Template

**Step 1: Immediate (Next 30 Days)**
• Document current tax situation
• Identify 2-3 highest-impact opportunities
• Gather necessary documentation

**Step 2: Short-term (3-6 Months)**
• Implement foundation strategies
• Set up necessary structures
• Begin tracking and measuring results

**Step 3: Long-term (6+ Months)**
• Monitor and adjust strategies
• Add growth layer strategies
• Plan for major upcoming events

## Moving Beyond the Course

You now have the framework to evaluate any tax strategy through the lens of the 6 levers. Every opportunity, every advisor recommendation, every major financial decision can be analyzed using this systematic approach.""",
                duration_minutes=50,
                order_index=5
            ),
            CourseContent(
                title="IRS Communication Basics",
                description="How to interpret and respond to IRS notices",
                content="Understanding IRS letters and notices is crucial. This lesson teaches you how to read IRS correspondence, identify urgent vs. routine notices, and respond appropriately.",
                duration_minutes=30,
                order_index=6
            ),
            CourseContent(
                title="Payment Options Overview",
                description="Explore different ways to resolve tax debt",
                content="The IRS offers several payment options including payment plans, offers in compromise, and currently not collectible status. Learn which option might work for your situation.",
                duration_minutes=35,
                order_index=7
            ),
            CourseContent(
                title="Professional Help: When and How",
                description="Understanding when to seek professional assistance",
                content="Some tax situations require professional help. Learn when to contact a tax professional, what credentials to look for, and how to work effectively with tax representatives.",
                duration_minutes=20,
                order_index=8
            ),
            CourseContent(
                title="Creating Your Action Plan",
                description="Develop a personalized strategy for your tax situation",
                content="Put everything together to create a step-by-step action plan tailored to your specific tax situation and goals.",
                duration_minutes=30,
                order_index=9
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
        title="Business Owner Escape Plan",
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
        # Module 1 Questions
        QuizQuestion(
            question="What's the biggest weakness of a traditional CPA?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["They cost too much", "They can't access your financials", "They focus on filing, not planning", "They don't understand deductions"],
            correct_answer="They focus on filing, not planning",
            explanation="Traditional CPAs focus on compliance and filing returns, while tax strategists focus on proactive planning to minimize future tax liability.",
            course_id=primer_course.id,
            module_id=1
        ),
        # Module 3 Questions
        QuizQuestion(
            question="What's the benefit of investing RSU capital gains into a QOF?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Locks in early retirement", "Defers capital gains and allows long-term tax-free growth", "Eliminates W-2 tax", "Converts gains into passive interest"],
            correct_answer="Defers capital gains and allows long-term tax-free growth",
            explanation="Qualified Opportunity Funds allow you to defer capital gains taxes and potentially eliminate them entirely if held for 10+ years, while the investment grows tax-free.",
            course_id=primer_course.id,
            module_id=3
        ),
        QuizQuestion(
            question="What's the function of routing income through a C-Corp MSO?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["To access SBA loans", "To avoid LLC fees", "To reposition retained earnings into tax-leveraged assets", "To create employee stock options"],
            correct_answer="To reposition retained earnings into tax-leveraged assets",
            explanation="A C-Corp MSO structure allows business owners to retain earnings at lower corporate tax rates and invest them in bonus depreciation assets for additional tax benefits.",
            course_id=primer_course.id,
            module_id=3
        ),
        QuizQuestion(
            question="How did Liam offset his W-2 income?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Oil & Gas credits", "Deductions from charity", "REPS status + STR depreciation", "Cost segregation of his home"],
            correct_answer="REPS status + STR depreciation",
            explanation="By qualifying for Real Estate Professional Status, Liam could use depreciation from his short-term rental properties to offset his W-2 income from his medical practice.",
            course_id=primer_course.id,
            module_id=3
        ),
        QuizQuestion(
            question="What is the IRS's primary function?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Protect taxpayers", "Penalize business owners", "Reconcile tax credits", "Collect revenue"],
            correct_answer="Collect revenue",
            explanation="The IRS's primary function is to collect revenue for the federal government through tax collection and enforcement.",
            course_id=primer_course.id,
            module_id=1
        ),
        QuizQuestion(
            question="The tax code is best understood as:",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["A punishment", "A charity tool", "A set of incentives", "A list of penalties"],
            correct_answer="A set of incentives",
            explanation="The tax code is designed as a blueprint for wealth-building behavior, rewarding investment, ownership, and risk-taking through various incentives.",
            course_id=primer_course.id,
            module_id=1
        ),
        # Module 2 Questions
        QuizQuestion(
            question="Which of the following is NOT one of the 6 tax control levers?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Entity Type", "Income Type", "Filing Method", "Exit Planning"],
            correct_answer="Filing Method",
            explanation="The 6 tax control levers are: Entity Type, Income Type, Timing, Asset Location, Deduction Strategy, and Exit Planning. Filing Method is not one of the core levers.",
            course_id=primer_course.id,
            module_id=2
        ),
        QuizQuestion(
            question="Why does income type matter?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Different income types get different tax treatments", "Income type sets your credit score", "It determines your CPA's fee", "It changes your audit rate"],
            correct_answer="Different income types get different tax treatments",
            explanation="Different types of income (W-2 wages, capital gains, dividends, rental income) are taxed at different rates and have different deduction opportunities.",
            course_id=primer_course.id,
            module_id=2
        ),
        QuizQuestion(
            question="What's the main reason timing is important in tax strategy?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["It affects bank interest", "It reduces IRS penalties", "It lets you control when income hits", "It locks in your deductions"],
            correct_answer="It lets you control when income hits",
            explanation="Strategic timing allows you to control when income is recognized, which can shift tax liability between years and optimize your overall tax burden.",
            course_id=primer_course.id,
            module_id=2
        ),
        # Module 4 Questions
        QuizQuestion(
            question="What determines your exposure to W-2 tax rates?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["CPA filing method", "The number of dependents", "Type and timing of income", "Your employer's tax strategy"],
            correct_answer="Type and timing of income",
            explanation="Your exposure to high W-2 tax rates is determined by the type of income you receive and when you receive it. Different income types have different tax treatments.",
            course_id=primer_course.id,
            module_id=4
        ),
        QuizQuestion(
            question="Which of the following directly impacts deduction limits?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Filing software", "Where you bank", "Your income type and asset structure", "Credit card rewards"],
            correct_answer="Your income type and asset structure",
            explanation="Deduction limits are directly impacted by your income type and how your assets are structured, as these determine what deductions you're eligible for and at what levels.",
            course_id=primer_course.id,
            module_id=4
        ),
        QuizQuestion(
            question="What is the first step to reducing your tax exposure?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["File early", "Review prior returns", "Map your income, entity, and deduction levers", "Ask your CPA to amend"],
            correct_answer="Map your income, entity, and deduction levers",
            explanation="The first step to reducing tax exposure is mapping your current situation across the 6 levers: income type, entity structure, timing, asset location, deductions, and exit planning.",
            course_id=primer_course.id,
            module_id=4
        ),
        # Module 5 Questions
        QuizQuestion(
            question="What determines which levers apply to you?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Your income type, entity structure, and timing flexibility", "Your age", "Your tax bracket", "Your CPA's filing software"],
            correct_answer="Your income type, entity structure, and timing flexibility",
            explanation="The levers that apply to your situation are determined by your specific income profile, current entity structure, and flexibility to control timing of income and deductions.",
            course_id=primer_course.id,
            module_id=5
        ),
        QuizQuestion(
            question="What's the purpose of building a glossary + case study reference set?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["To impress your CPA", "To help you align the right tools and strategies with your profile", "To get better IRS emails", "To automatically lower AGI"],
            correct_answer="To help you align the right tools and strategies with your profile",
            explanation="Building a reference set helps you match the most appropriate strategies and tools to your specific tax situation and profile type.",
            course_id=primer_course.id,
            module_id=5
        ),
        QuizQuestion(
            question="What is the goal of an Escape Plan?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["To avoid taxes forever", "To replace CPAs", "To apply the tax code proactively and reduce lifetime tax burden", "To defer all income"],
            correct_answer="To apply the tax code proactively and reduce lifetime tax burden",
            explanation="The goal of an Escape Plan is to use the tax code's existing incentives proactively to legally minimize your lifetime tax burden through strategic planning.",
            course_id=primer_course.id,
            module_id=5
        )
    ]
    
    for question in quiz_questions:
        await db.quiz_questions.insert_one(question.dict())
    
    # Sample glossary terms
    glossary_terms = [
        GlossaryTerm(
            term="Tax Planning",
            definition="Proactively structuring income and assets to legally reduce taxes through strategic timing, entity selection, and asset positioning.",
            category="Tax Strategy",
            related_terms=["CPA vs Strategist", "W-2 Income", "Tax Strategy"]
        ),
        GlossaryTerm(
            term="W-2 Income",
            definition="Employee wages that are taxed at the highest effective rate with limited deduction opportunities and no control over timing.",
            category="Income Types",
            related_terms=["Tax Planning", "Business Income", "1099 Income"]
        ),
        GlossaryTerm(
            term="CPA vs Strategist",
            definition="CPAs focus on compliance and filing returns after the fact. Tax strategists proactively plan and structure to minimize future tax liability before income is earned.",
            category="Professional Services",
            related_terms=["Tax Planning", "Tax Strategy", "Proactive Planning"]
        ),
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
        ),
        GlossaryTerm(
            term="Entity Planning",
            definition="Strategic selection and structuring of business entities (LLC, S-Corp, C-Corp, Partnership) to optimize tax treatment based on income type, business activities, and long-term goals.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "Business Structure", "Income Type"]
        ),
        GlossaryTerm(
            term="Income Shifting",
            definition="Legal strategies to convert high-tax income types (like W-2 wages) into lower-tax income types (like capital gains or qualified dividends) through proper structuring.",
            category="Tax Strategy",
            related_terms=["Income Type", "Tax Planning", "W-2 Income"]
        ),
        GlossaryTerm(
            term="Timing Arbitrage",
            definition="Strategic control of when income and deductions are recognized to optimize tax liability across multiple years and take advantage of rate differences.",
            category="Advanced Strategy",
            related_terms=["Tax Planning", "Income Shifting", "Strategic Deductions"]
        ),
        GlossaryTerm(
            term="Asset Location",
            definition="The strategic placement of different investment types in tax-advantaged vs. taxable accounts to minimize overall tax burden and maximize after-tax returns.",
            category="Investment Strategy",
            related_terms=["Tax Planning", "Investment Tax", "Retirement Planning"]
        ),
        GlossaryTerm(
            term="Strategic Deductions",
            definition="Proactive structuring and timing of business and investment expenses to maximize tax deductions while maintaining proper documentation and compliance.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "Business Deductions", "Timing Arbitrage"]
        ),
        GlossaryTerm(
            term="Exit Structuring",
            definition="Strategic planning for how to exit investments, businesses, or transfer wealth to minimize tax impact and maximize after-tax proceeds for beneficiaries.",
            category="Advanced Strategy",
            related_terms=["Tax Planning", "Estate Planning", "Capital Gains"]
        ),
        GlossaryTerm(
            term="Qualified Opportunity Fund",
            definition="A tax-advantaged investment vehicle that allows investors to defer and potentially eliminate capital gains taxes by investing in designated low-income communities for 10+ years.",
            category="Advanced Strategy",
            related_terms=["Capital Gains", "Tax Deferral", "Investment Strategy"]
        ),
        GlossaryTerm(
            term="Bonus Depreciation",
            definition="A tax incentive that allows businesses to immediately deduct a large percentage (often 100%) of eligible asset purchases in the year of acquisition, rather than depreciating over time.",
            category="Business Tax",
            related_terms=["Depreciation", "Business Deductions", "Strategic Deductions"]
        ),
        GlossaryTerm(
            term="REPS",
            definition="Real Estate Professional Status - A tax classification that allows qualifying individuals to deduct rental real estate losses against other income, including W-2 wages.",
            category="Real Estate Tax",
            related_terms=["Real Estate", "W-2 Income", "Depreciation Offset"]
        ),
        GlossaryTerm(
            term="Depreciation Offset",
            definition="Using depreciation deductions from real estate or business assets to reduce taxable income from other sources, such as W-2 wages or business profits.",
            category="Tax Strategy",
            related_terms=["REPS", "Real Estate", "Strategic Deductions"]
        ),
        GlossaryTerm(
            term="STR",
            definition="Short-Term Rental - Rental properties (like Airbnb) rented for less than 30 days, which receive favorable tax treatment including accelerated depreciation and business expense deductions.",
            category="Real Estate Tax",
            related_terms=["Real Estate", "REPS", "Depreciation Offset"]
        ),
        GlossaryTerm(
            term="AGI",
            definition="Adjusted Gross Income - Your total income minus specific deductions allowed by the IRS. AGI determines your tax bracket and eligibility for various deductions and credits.",
            category="Tax Terms",
            related_terms=["Gross Income", "Deductions", "Tax Liability", "Income Type Stack"]
        ),
        GlossaryTerm(
            term="Deduction Bandwidth",
            definition="The gap between what you're currently claiming in deductions and what you could legally claim with proper structuring and planning. Most high earners have significant unused deduction bandwidth.",
            category="Tax Strategy",
            related_terms=["Strategic Deductions", "Tax Planning", "Business Deductions"]
        ),
        GlossaryTerm(
            term="Income Type Stack",
            definition="The combination and layering of different income types (W-2, 1099, K-1, capital gains, passive) that determines not just how much tax you pay, but when you pay it and what deductions are available.",
            category="Tax Strategy",
            related_terms=["Income Shifting", "W-2 Income", "AGI", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Entity Exposure",
            definition="The risk and inefficiency created by operating under a suboptimal business entity structure for your income level and business activities. Higher income often requires more sophisticated entity structures.",
            category="Business Tax",
            related_terms=["Entity Planning", "Business Structure", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Tax Exposure",
            definition="The total amount of tax liability you face based on your current income structure, entity choices, and planning strategies. Reducing tax exposure is the goal of strategic tax planning.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "AGI", "Entity Exposure", "Deduction Bandwidth"]
        ),
        GlossaryTerm(
            term="Lever Hierarchy",
            definition="The prioritized ranking of which of the 6 tax levers will have the most impact for your specific situation, based on your income type, entity structure, and goals.",
            category="Strategic Framework",
            related_terms=["Tax Planning", "Strategy Stack", "Personalized Planning"]
        ),
        GlossaryTerm(
            term="Personalized Planning",
            definition="Customized tax strategy development based on your specific income profile, entity structure, goals, and circumstances rather than generic tax advice.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "Lever Hierarchy", "Strategy Stack", "Advisor Integration"]
        ),
        GlossaryTerm(
            term="Strategy Stack",
            definition="A layered approach to tax optimization that combines multiple strategies across foundation, growth, and advanced levels for maximum tax reduction.",
            category="Strategic Framework",
            related_terms=["Lever Hierarchy", "Personalized Planning", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Advisor Integration",
            definition="The strategic coordination between different tax professionals (CPAs, strategists, attorneys) to ensure compliance while maximizing tax optimization opportunities.",
            category="Professional Services",
            related_terms=["CPA vs Strategist", "Tax Planning", "Personalized Planning"]
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
