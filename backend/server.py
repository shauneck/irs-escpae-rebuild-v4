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

# User XP and tracking models
class UserXP(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For demo purposes
    total_xp: int = 0
    quiz_xp: int = 0
    glossary_xp: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class MarketplaceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    category: str
    is_featured: bool = False
    image_url: Optional[str] = None

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

@api_router.get("/glossary/{term_id}", response_model=GlossaryTerm)
async def get_glossary_term(term_id: str):
    term = await db.glossary.find_one({"id": term_id})
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return GlossaryTerm(**term)

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

# XP tracking endpoints
@api_router.get("/users/xp/{user_id}")
async def get_user_xp(user_id: str):
    user_xp = await db.user_xp.find_one({"user_id": user_id})
    if not user_xp:
        # Create default XP record if it doesn't exist
        new_xp = UserXP(user_id=user_id)
        await db.user_xp.insert_one(new_xp.dict())
        return new_xp
    return UserXP(**user_xp)

@api_router.get("/users/xp")
async def get_default_user_xp():
    return await get_user_xp("default_user")

class XPRequest(BaseModel):
    user_id: str = "default_user"
    term_id: Optional[str] = None
    points: Optional[int] = None

@api_router.post("/users/xp/glossary")
async def award_glossary_xp(request: XPRequest):
    """Award 5 XP for viewing a glossary term"""
    user_xp = await db.user_xp.find_one({"user_id": request.user_id})
    if not user_xp:
        new_xp = UserXP(user_id=request.user_id, glossary_xp=5, total_xp=5)
        await db.user_xp.insert_one(new_xp.dict())
        return {"status": "success", "xp_earned": 5, "total_xp": 5}
    else:
        new_glossary_xp = user_xp["glossary_xp"] + 5
        new_total_xp = user_xp["total_xp"] + 5
        await db.user_xp.update_one(
            {"user_id": request.user_id},
            {"$set": {
                "glossary_xp": new_glossary_xp,
                "total_xp": new_total_xp,
                "last_updated": datetime.utcnow()
            }}
        )
        return {"status": "success", "xp_earned": 5, "total_xp": new_total_xp}

@api_router.post("/users/xp/quiz")
async def award_quiz_xp(request: XPRequest):
    """Award XP for quiz completion"""
    points = request.points or 10  # Default 10 points for quiz
    user_xp = await db.user_xp.find_one({"user_id": request.user_id})
    if not user_xp:
        new_xp = UserXP(user_id=request.user_id, quiz_xp=points, total_xp=points)
        await db.user_xp.insert_one(new_xp.dict())
        return {"status": "success", "xp_earned": points, "total_xp": points}
    else:
        new_quiz_xp = user_xp["quiz_xp"] + points
        new_total_xp = user_xp["total_xp"] + points
        await db.user_xp.update_one(
            {"user_id": request.user_id},
            {"$set": {
                "quiz_xp": new_quiz_xp,
                "total_xp": new_total_xp,
                "last_updated": datetime.utcnow()
            }}
        )
        return {"status": "success", "xp_earned": points, "total_xp": new_total_xp}

# Marketplace endpoints
@api_router.get("/marketplace", response_model=List[MarketplaceItem])
async def get_marketplace():
    items = await db.marketplace.find().to_list(1000)
    return [MarketplaceItem(**item) for item in items]

@api_router.get("/marketplace/{item_id}", response_model=MarketplaceItem)
async def get_marketplace_item(item_id: str):
    item = await db.marketplace.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Marketplace item not found")
    return MarketplaceItem(**item)

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
    await db.marketplace.delete_many({})
    await db.user_xp.delete_many({})
    
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
                title="Why You're Overpaying the IRS (and What to Do About It)",
                description="Module 1 of 5 - Discover why the tax code rewards wealth-building behavior and how strategists differ from traditional CPAs",
                content="""The U.S. tax code is not a punishment — it's a blueprint for wealth-building behavior. It rewards investment, ownership, and risk — and penalizes passive employment without structure.

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

### 1. Entity Type
• Your **entity structure** determines your tax ceiling.
• C-Corp, S-Corp, MSO, or Schedule C — they're not all created equal.
• Strategically managing entity types is how business owners avoid double taxation and unlock deduction control.

### 2. Income Type
• Not all income is taxed equally.
• W-2, 1099, K-1, capital gains, passive flow — each has a different tax treatment.
• You don't need to earn less. You need to earn differently.

### 3. Timing
• Tax timing is a weapon — not a constraint.
• Installment sales, deferred comp, Roth conversions, asset rollovers all leverage when income hits.

### 4. Asset Location
• Where your assets live changes how they're taxed.
• Insurance wrappers, retirement accounts, real estate, and **Opportunity Zones** all have unique benefits.

### 5. Deduction Strategy
• Most CPAs miss over 50% of the deductions available.
• True planning involves orchestrating deductions through energy, depreciation, trust layering, and timing.

### 6. Exit Planning
• If you build wealth but don't plan your exit, the IRS cashes out with you.
• QSBS, Opportunity Zones, charitable trusts, and stepped-up basis strategy all come into play here.

## Application

These levers apply to:
• ✅ Business owners shifting to MSO or C-Corp models
• ✅ W-2 earners creating deduction pathways using **asset location**
• ✅ Real estate professionals leveraging depreciation
• ✅ Exit events (business sale, asset sale, vesting RSUs)

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

This module walks through anonymized client case studies that reflect exactly how the 6 levers are used in real scenarios. These examples will show you how a shift in entity, income type, deduction strategy, or timing can result in transformational tax savings.

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
• Retained earnings invested into Oil & Gas and equipment **bonus depreciation**
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

Understanding your profile type determines which strategies will have the biggest impact on your tax exposure:

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

Not all levers are equally valuable for your situation. Your Lever Hierarchy prioritizes where to focus first:

### High-Impact Levers (Start Here)
**For W-2 Earners:**
1. Deduction Strategy - Maximize available deductions
2. Asset Location - Optimize account placement
3. Timing - Control when income hits

**For Business Owners:**
1. Entity Type - Optimize business structure
2. Exit Planning - Plan for business growth and sale
3. Deduction Strategy - Maximize business deductions

**For Investors:**
1. Asset Location - Strategic account management
2. Timing - Harvest losses and control recognition
3. Income Type - Convert ordinary income to capital gains

### Your **Strategy Stack**

Your Strategy Stack combines multiple approaches for maximum impact:

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

You now have the framework to evaluate any tax strategy through the lens of the 6 levers. Every opportunity, every advisor recommendation, every major financial decision can be analyzed using this systematic approach.

## Your Escape Plan is Complete

You've built your foundation. You've seen the levers. You've reviewed real case studies. And now — you've drafted your own escape framework.

From here, you unlock access to:
• **The full IRS Escape Plan course tracks** (W-2 and Business Owner)
• **Strategy tools** tailored to your profile
• **Personalized glossary and playbook dashboards**

**Let's move from course to command. Your plan starts now.**""",
                duration_minutes=50,
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
                title="The Real Problem with W-2 Income",
                description="Module 1 of 8 - W-2 Income Mapping - Understand the disadvantages of W-2 income and discover strategic alternatives",
                content="""The **W-2 income** structure is designed for maximum tax extraction with minimal taxpayer control. Understanding why W-2 income is taxed the way it is — and what alternatives exist — is the first step to building a strategic escape plan.

Most W-2 earners accept their tax situation as unchangeable. This module shows you why that's not true, and how strategic planning can transform your **effective tax rate** even while maintaining W-2 employment.

## The W-2 Disadvantage

**W-2 income** faces the highest effective tax rates in the U.S. tax system:

### 1. **Limited Deduction Control**
• Most W-2 expenses are non-deductible after the 2017 Tax Cuts and Jobs Act
• No control over payroll tax timing or deferral
• Minimal opportunity for depreciation or timing strategies

### 2. **Immediate Tax Recognition**
• Taxes withheld from every paycheck with no deferral options
• No control over when income hits your tax return
• Limited ability to shift income between tax years

### 3. **No Entity Leverage**
• Unable to access business deductions without additional structure
• No path to corporate tax rates or retained earnings benefits
• Limited asset protection and wealth-building tax incentives

### 4. **Payroll Tax Exposure**
• Subject to full Social Security and Medicare taxes (15.3% combined employer/employee)
• No strategies to reduce FICA exposure without business structure

## W-2 Profile Mapping Exercise

Understanding your W-2 profile helps identify which escape strategies will have the biggest impact:

### **High-Income W-2 ($200K+)**
**Primary Challenges:**
• High marginal tax rates (32-37%)
• Limited deduction opportunities
• Potential for RSU or bonus income creating tax spikes

**Primary Opportunities:**
• **Real estate depreciation** strategies through STR or rental properties
• Strategic timing of equity compensation
• Qualified retirement plan contributions and backdoor Roth strategies

### **W-2 + Side Business**
**Primary Challenges:**
• Mixing W-2 and business income creates complexity
• Self-employment tax on business income
• Limited business deduction opportunities without proper structure

**Primary Opportunities:**
• **Entity planning** to optimize business structure
• Business expense deductions to offset W-2 income
• Strategic equipment purchases for **bonus depreciation**

### **W-2 + Investment Income**
**Primary Challenges:**
• Multiple income types with different tax treatments
• Potential for higher Medicare surtaxes (3.8% NIIT)
• Complex tax planning across different asset classes

**Primary Opportunities:**
• **Asset location** strategies across account types
• Tax-loss harvesting and gain/loss timing
• Opportunity Zone investments for capital gains deferral

## Case Study: Olivia – Tech Sales Executive

**Background:**
Olivia earns $180K in W-2 income plus $220K in annual RSU vesting from her tech company. Her **effective tax rate** was 34% before implementing strategic planning.

**The Problem:**
• High ordinary income tax rates on W-2 wages
• Large capital gains from RSU vesting creating tax spikes
• Limited deduction opportunities as a W-2 employee
• No strategic planning beyond standard 401(k) contributions

**The Strategy:**
1. **QOF Investment:** Used RSU gains to fund a **Qualified Opportunity Fund** investment, deferring $220K in capital gains
2. **STR Investment:** QOF proceeds invested in short-term rental properties
3. **REPS Qualification:** Qualified for **Real Estate Professional Status** through material participation
4. **Depreciation Offset:** STR depreciation offsets W-2 income dollar-for-dollar

**The Results:**
• **Effective tax rate** dropped from 34% to 21%
• $220K in capital gains deferred for 10+ years
• $48K in annual STR depreciation offsetting W-2 income
• Built a growing real estate portfolio through tax-advantaged investment

**Key Insight:** Even high-income W-2 earners can access sophisticated tax strategies through proper structuring and **forward-looking planning**.

## Strategic Alternatives to W-2 Limitations

### **Real Estate Professional Status (REPS)**
• Qualify through material participation in real estate activities
• Use rental property depreciation to offset W-2 income
• Build long-term wealth through appreciating assets

### **Business Entity Creation**
• Establish side businesses to access business deductions
• Convert personal expenses into legitimate business deductions
• Create pathways to more sophisticated tax planning

### **Investment Structure Optimization**
• Strategic use of retirement accounts vs. taxable accounts
• Tax-loss harvesting and gain recognition timing
• Opportunity Zone investments for capital gains management

### **Timing and Deferral Strategies**
• Strategic timing of equity compensation vesting
• Deferred compensation arrangements where available
• Charitable giving strategies for high-income years

## The **Forward-Looking Planning** Approach

Traditional **CPA vs Strategist** differences are most apparent with W-2 income:

**Traditional CPA Approach:**
• File W-2 returns as received
• Maximize standard or itemized deductions
• Focus on compliance and current-year filing

**Strategic Tax Planning Approach:**
• Proactively structure additional income sources
• Create deduction opportunities through proper entity planning
• Implement multi-year tax optimization strategies
• Use W-2 income as foundation for broader wealth-building tax strategies

## Your W-2 Escape Framework

**Phase 1: Assessment (Months 1-2)**
• Calculate your true **effective tax rate** including all taxes
• Identify your W-2 profile type and primary limitations
• Evaluate current deduction bandwidth and missed opportunities

**Phase 2: Foundation Building (Months 3-6)**
• Implement immediate deduction optimization strategies
• Establish business entities or real estate investments if applicable
• Optimize retirement account contributions and asset location

**Phase 3: Advanced Structuring (Months 6-12)**
• Implement real estate or business depreciation strategies
• Execute timing optimization for equity compensation
• Build systematic approach to ongoing tax planning

## What's Next

You don't need to abandon your W-2 career to escape W-2 tax limitations. Strategic planning creates opportunities to:

• **Reduce your effective tax rate** through depreciation and timing strategies
• **Build wealth** through tax-advantaged real estate and business investments  
• **Create long-term tax benefits** that compound over time

In Module 2, we'll dive deep into the specific deduction strategies available to W-2 earners and show you how to implement them systematically.

**Your W-2 escape plan starts with understanding that your current tax situation is a choice, not a limitation.**

---

🎯 **Ready to test your knowledge?** Take the Module 1 quiz to earn +50 XP and reinforce these key concepts before moving to Module 2.""",
                duration_minutes=45,
                order_index=1
            ),
            CourseContent(
                title="Repositioning W-2 Income for Strategic Impact",
                description="Module 2 of 8 - Repositioning RSUs & Bonus Income - Learn advanced strategies to reposition already-taxed W-2 income for maximum tax benefits",
                content="""After understanding the fundamental limitations of **W-2 income** in Module 1, the next step is learning how to **reposition** already-taxed income for strategic tax advantages. This isn't about avoiding the initial tax hit—it's about ensuring every dollar you've already paid taxes on works as hard as possible to reduce your future tax burden.

**Repositioning** transforms passive, already-taxed income into active, tax-advantaged investments that generate ongoing deductions and long-term wealth building opportunities.

## The Repositioning Framework

Most W-2 earners think their tax planning ends when they receive their paycheck. Strategic repositioning shows that's actually where the real opportunities begin.

### What is **Repositioning**?

**Repositioning** is the strategic deployment of already-taxed W-2 income into investments and structures that generate:
• **Immediate tax deductions** through depreciation and business expenses
• **Ongoing passive income** with favorable tax treatment
• **Long-term wealth building** through appreciating assets
• **Future tax deferral** opportunities through strategic timing

### The Three Pillars of W-2 Repositioning

**1. Capital Gain Optimization**
Using equity compensation and bonuses to fund tax-advantaged investments like **Qualified Opportunity Funds (QOF)** for **capital gain deferral**.

**2. Depreciation Harvesting**
Converting cash into depreciable assets (primarily **Short-Term Rental (STR)** properties) to generate **depreciation losses** that offset W-2 income.

**3. Business Structure Integration**
Creating legitimate business activities that allow personal expenses to become business deductions while building long-term asset value.

## Understanding **Qualified Opportunity Funds (QOF)**

**Qualified Opportunity Funds (QOF)** represent one of the most powerful tools for W-2 earners with significant capital gains from equity compensation.

### QOF Benefits for W-2 Earners:

**Immediate Capital Gain Deferral:**
• Defer capital gains taxes until December 31, 2026 (or sale of QOF investment)
• No limits on the amount of gains that can be deferred
• Works with RSU sales, ESPP gains, and other equity compensation

**Step-Up in Basis Benefits:**
• 10% step-up in basis after 5 years of investment
• 15% step-up in basis after 7 years of investment
• Complete elimination of capital gains tax on QOF appreciation after 10 years

**Strategic W-2 Integration:**
• Use QOF proceeds to invest in **Short-Term Rental (STR)** properties
• Generate **material participation** income to offset W-2 wages
• Create systematic **depreciation losses** for ongoing tax benefits

## **Short-Term Rental (STR)** Strategy for W-2 Earners

**Short-Term Rental (STR)** properties offer W-2 earners the most direct path to generating **depreciation losses** that can offset ordinary income.

### STR Advantages Over Traditional Rentals:

**Higher Income Potential:**
• 2-4x rental income compared to long-term rentals
• Premium pricing for furnished, managed properties
• Multiple revenue streams (nightly, weekly, monthly bookings)

**Enhanced Depreciation Benefits:**
• **Bonus depreciation** on furniture, fixtures, and equipment
• Shorter depreciable lives for personal property (5-7 years vs 27.5 years)
• Cost segregation opportunities for maximum first-year deductions

**Business Expense Opportunities:**
• Travel to properties for "inspection and maintenance"
• Professional development and education expenses
• Technology and software for property management

### **Material Participation** Requirements

To use **STR** **depreciation losses** against W-2 income, you must qualify for **material participation**:

**750-Hour Rule:**
• Spend 750+ hours annually in short-term rental activities
• Document time through detailed logs and records
• Include property search, management, maintenance, and guest services

**Business Activities That Count:**
• Property research and acquisition
• Guest communication and booking management
• Property maintenance and improvements
• Marketing and listing optimization
• Financial record keeping and tax preparation

## Case Study: Helen (Part 2 of 9) - RSUs + STR + QOF Strategy

**Background:**
Helen is a senior software engineer at a tech company earning $160K in W-2 wages plus $180K annually in RSU vesting. She's been accumulating RSUs for three years and wants to optimize her tax strategy while building long-term wealth.

**The Challenge:**
• $540K in accumulated RSU gains ready to vest
• Facing $183K in capital gains taxes (34% effective rate)
• Limited deduction opportunities as a W-2 employee
• Wants to build real estate wealth while reducing current tax burden

**The Repositioning Strategy:**

**Phase 1: QOF Capital Gain Deferral**
• Sell $540K in RSUs and immediately invest proceeds in a **Qualified Opportunity Fund (QOF)**
• **Defer $183K in capital gains taxes** until December 31, 2026
• QOF invests in opportunity zone real estate development projects

**Phase 2: STR Property Acquisition**
• Use QOF investment returns and additional savings to acquire $1.2M in **Short-Term Rental (STR)** properties
• Purchase 3 properties in high-demand vacation rental markets
• Finance with 25% down payments to maximize leverage and cash flow

**Phase 3: Material Participation & Depreciation**
• Establish **material participation** by logging 800+ hours annually in STR activities
• Generate $156K in annual **depreciation losses** through:
  - Building depreciation: $87K annually
  - **Bonus depreciation** on furnishings: $45K first year
  - Equipment and technology: $24K annually

**Phase 4: W-2 Income Offset**
• Use $156K in **depreciation losses** to offset $160K in W-2 wages
• Effectively reduce taxable income from $160K to $4K
• Maintain full STR cash flow while eliminating W-2 tax burden

**The Results After 18 Months:**

**Tax Savings:**
• **$183K in capital gains taxes deferred** through QOF strategy
• **$53K annual W-2 tax savings** through STR depreciation offset
• **$89K in total tax burden reduction** in first 18 months

**Wealth Building:**
• $1.2M in appreciating real estate assets
• $84K annual cash flow from STR operations
• $540K QOF investment with potential for tax-free growth after 10 years

**Strategic Position:**
• Diversified investment portfolio beyond tech stock concentration
• Multiple income streams reducing W-2 dependency
• Established business activities creating ongoing deduction opportunities

**Key Insight:** Helen transformed $540K in taxable capital gains into a comprehensive wealth-building strategy that eliminated her W-2 tax burden while creating multiple streams of passive income and long-term asset appreciation.

## Advanced Repositioning Strategies

### **Bonus Depreciation** Optimization

**Equipment and Technology Purchases:**
• Computer equipment and software for STR management
• Furniture and fixtures for rental properties
• Vehicles used for property management activities

**Timing Strategies:**
• Purchase qualifying assets before December 31st for current-year deductions
• Coordinate large purchases with high-income years
• Use cost segregation studies to maximize depreciable basis

### **Capital Gain Deferral** Through Strategic Timing

**RSU Vesting Coordination:**
• Time RSU sales to coordinate with QOF investment opportunities
• Stagger sales across multiple years to optimize tax brackets
• Use tax-loss harvesting to offset gains in non-QOF years

**1031 Exchange Integration:**
• Use like-kind exchanges for traditional rental properties
• Coordinate with STR acquisition for maximum deferral benefits
• Build portfolio diversity through strategic property exchanges

### Business Entity Integration

**LLC Structure for STR Activities:**
• Establish separate LLCs for each property or property group
• Optimize for liability protection and tax efficiency
• Enable pass-through taxation while maintaining business expense deductions

**Professional Development Deductions:**
• Real estate education and certification programs
• Property management conferences and networking events
• Technology and software training for business optimization

## Implementation Timeline for W-2 Repositioning

### **Months 1-3: Foundation Building**
• **Asset Assessment:** Calculate total equity compensation and capital gains exposure
• **Strategy Selection:** Choose between QOF, direct STR investment, or hybrid approach
• **Professional Team:** Assemble tax strategist, real estate agent, and property manager

### **Months 4-6: Strategic Execution**
• **Capital Deployment:** Execute QOF investment or direct property acquisition
• **Structure Setup:** Establish business entities and operational systems
• **Documentation Systems:** Implement time tracking and expense recording procedures

### **Months 7-12: Optimization & Scaling**
• **Material Participation:** Meet and document 750+ hour requirements
• **Depreciation Maximization:** Implement cost segregation and bonus depreciation strategies
• **Performance Monitoring:** Track cash flow, tax savings, and asset appreciation

### **Year 2+: Advanced Strategies**
• **Portfolio Expansion:** Add properties or increase QOF investments
• **Entity Optimization:** Refine business structures for maximum efficiency
• **Exit Planning:** Prepare for QOF step-up benefits and long-term wealth realization

## Common W-2 Repositioning Mistakes to Avoid

### **Insufficient Material Participation Documentation**
• **Problem:** Failing to meet or document 750+ hour requirement
• **Solution:** Implement systematic time tracking from day one
• **Best Practice:** Log activities in real-time using dedicated apps or spreadsheets

### **Over-Leveraging on Property Acquisition**
• **Problem:** Taking on too much debt relative to cash flow capacity
• **Solution:** Maintain conservative loan-to-value ratios (75% or less)
• **Best Practice:** Ensure properties cash flow positive even during low occupancy periods

### **Mixing Personal and Business Activities**
• **Problem:** Using STR properties for personal vacations without proper documentation
• **Solution:** Establish clear business use policies and maintain detailed records
• **Best Practice:** Treat STR activities as legitimate business operations from day one

## Measuring Repositioning Success

### **Tax Efficiency Metrics**
• **Effective Tax Rate Reduction:** Target 15-25% reduction in overall tax burden
• **Depreciation Utilization:** Maximize allowable depreciation against W-2 income
• **Capital Gain Deferral:** Optimize timing and amount of deferred gains

### **Wealth Building Indicators**
• **Cash Flow Growth:** Target 8-12% annual cash-on-cash returns from STR properties
• **Asset Appreciation:** Monitor property value growth and QOF performance
• **Portfolio Diversification:** Reduce dependency on W-2 income over time

### **Strategic Positioning Goals**
• **Income Stream Diversity:** Build multiple sources of passive income
• **Tax Strategy Sophistication:** Develop repeatable systems for ongoing optimization
• **Long-Term Financial Independence:** Create pathway to reduce W-2 dependency

## What's Next: Advanced Entity Strategies

Module 2 has shown you how to **reposition** your already-taxed W-2 income for maximum strategic impact. In Module 3, we'll explore advanced entity strategies that allow W-2 earners to create additional income streams while accessing business-level tax deductions.

**Key Takeaway:** **Repositioning** isn't about avoiding taxes—it's about ensuring every tax dollar you've already paid works strategically to reduce your future tax burden while building long-term wealth.

The most successful W-2 earners don't just earn and save—they systematically **reposition** their income for maximum tax advantage and wealth creation.

---

🎯 **Ready to test your repositioning knowledge?** Take the Module 2 quiz to earn +50 XP and solidify these advanced concepts before diving into Module 3's entity strategies.""",
                duration_minutes=50,
                order_index=2
            ),
            CourseContent(
                title="Stacking Offsets — The Tax Strategy Most W-2 Earners Miss",
                description="Module 3 of 8 - Offset Layering - Learn advanced offset stacking strategies to maximize deductions and continue Helen's Year 2 implementation",
                content="""Most W-2 earners who discover one tax strategy stop there. They find **depreciation offset** from short-term rentals and think they've maximized their opportunities. But the most sophisticated W-2 tax planners understand **offset stacking** — systematically layering multiple deduction strategies to create a comprehensive **deduction portfolio**.

**Offset stacking** allows high-income W-2 earners to build multiple streams of tax deductions that work together synergistically, creating far more tax savings than any single strategy alone.

## Understanding **Offset Stacking**

**Offset stacking** is the strategic combination of multiple tax deduction sources to maximize overall tax benefit. Rather than relying on a single deduction type, successful W-2 earners build portfolios of complementary strategies.

### The Three Pillars of Effective Offset Stacking

**1. Primary Offset (Real Estate Depreciation)**
• **Short-Term Rental (STR)** depreciation as the foundation
• Reliable, recurring annual deductions
• Material participation qualification for W-2 offset capability

**2. Secondary Offset (Energy/Resource Investments)**
• **Intangible Drilling Costs (IDCs)** from oil and gas investments
• Renewable energy depreciation and tax credits
• Equipment and infrastructure depreciation

**3. Tertiary Offset (Business and Equipment)**
• Business entity depreciation and expenses
• Equipment purchases with **bonus depreciation**
• Professional development and training deductions

### Why Single-Strategy Approaches Fall Short

**The Depreciation Limitation Problem:**
Even with substantial STR investments, **depreciation offset** alone may not fully optimize tax savings for high-income W-2 earners earning $300K+ annually.

**Income Growth Challenges:**
• As W-2 income increases, single-strategy deductions become insufficient
• Bonus years and equity compensation create tax spikes requiring additional offsets
• **Carryforward loss** limitations restrict single-year deduction benefits

**Risk Concentration Issues:**
• Over-reliance on real estate market performance
• Single asset class exposure
• Limited diversification of deduction sources

## Case Study: Helen (Part 3 of 9) - Year 2 Offset Stacking Implementation

**Helen's Year 1 Recap:**
• Successfully implemented QOF + STR strategy
• Generated $156K in annual STR depreciation
• Offset her $160K W-2 income to near-zero taxable income
• Built $1.2M real estate portfolio generating $84K annual cash flow

**The Year 2 Challenge:**
Helen received a promotion increasing her W-2 income to $220K plus a $150K equity bonus. Her existing STR depreciation, while substantial, would no longer fully offset her increased income.

**Year 2 Strategy: Systematic Offset Stacking**

**Phase 1: STR Portfolio Expansion**
• Acquired additional $800K in STR properties using Year 1 cash flow
• Generated additional $67K in annual **depreciation offset**
• Total STR depreciation: $223K annually ($156K + $67K)

**Phase 2: Energy Investment Integration**
• Invested $250K in qualified oil and gas drilling projects
• Utilized **Intangible Drilling Costs (IDCs)** for immediate deductions
• Generated $175K in first-year **IDCs** deductions
• Ongoing depletion deductions for future years

**Phase 3: Equipment and Technology Offset**
• Purchased $45K in STR property equipment and technology
• Applied **bonus depreciation** for 100% first-year deduction
• Enhanced property management efficiency and guest experience

**Year 2 Total Deduction Strategy:**
• STR Depreciation: $223K
• Energy IDCs: $175K
• Equipment Depreciation: $45K
• **Total Offset Capacity: $443K**

**Year 2 Income vs. Deductions:**
• W-2 Income: $220K
• Equity Bonus: $150K
• **Total Taxable Income: $370K**
• **Total Deductions: $443K**
• **Net Taxable Income: $0** (with $73K **carryforward loss** for Year 3)

**Results After Two Years:**
• **$0 federal income tax** on $370K of Year 2 income
• **$73K carryforward loss** available for future high-income years
• **$2M+ asset portfolio** generating $127K annual cash flow
• **Diversified deduction sources** reducing single-strategy risk

## Advanced **Offset Stacking** Strategies

### **Depreciation Offset** Optimization

**Cost Segregation Maximization:**
• Accelerate depreciation on real estate improvements
• Separate land improvements from building basis
• Maximize short-term depreciation categories

**Asset Classification Strategies:**
• Separate personal property from real property
• Optimize furniture, fixtures, and equipment depreciation
• Coordinate timing for maximum current-year benefit

### **Intangible Drilling Costs (IDCs)** Integration

**Strategic IDC Deployment:**
• Time investments to coordinate with high-income years
• Stack IDCs with existing depreciation strategies
• Utilize working interest structures for maximum deduction benefit

**Risk Management Approaches:**
• Diversify across multiple drilling projects
• Balance exploration vs. development opportunities
• Coordinate with overall investment portfolio risk profile

### **Carryforward Loss** Management

**Multi-Year Tax Planning:**
• Generate excess deductions in high-income years
• Carry forward losses to offset future income spikes
• Coordinate with equity compensation timing

**Loss Utilization Optimization:**
• Prioritize highest-rate income for offset
• Coordinate state and federal tax benefits
• Plan for potential tax law changes

## Building Your **Deduction Portfolio**

### Year 1: Foundation Building
**Primary Focus: STR Implementation**
• Establish material participation qualification
• Generate base **depreciation offset** of $100K-200K annually
• Build operational systems and professional relationships

**Secondary Preparation:**
• Research energy investment opportunities
• Establish business entities for future strategies
• Build liquidity for additional investments

### Year 2: Portfolio Expansion
**Primary Expansion: Additional STR Properties**
• Scale existing successful strategies
• Optimize for cash flow and depreciation balance
• Enhance property management efficiencies

**Secondary Integration: Energy Investments**
• Add **IDCs** for immediate deduction benefits
• Diversify offset sources beyond real estate
• Create **carryforward loss** buffer for future years

### Year 3+: Advanced Optimization
**Strategy Refinement:**
• Optimize timing of various deduction strategies
• Coordinate with income spikes and equity compensation
• Build systematic approach to ongoing **offset stacking**

**Portfolio Management:**
• Monitor and adjust deduction mix based on income changes
• Plan for asset sales and basis recovery
• Prepare for long-term wealth transition strategies

## Common **Offset Stacking** Mistakes to Avoid

### **Over-Concentration in Single Strategy**
• **Problem:** Relying too heavily on STR depreciation alone
• **Solution:** Systematically diversify deduction sources
• **Best Practice:** Target 3-4 different offset strategies

### **Poor Timing Coordination**
• **Problem:** Generating deductions when income is low
• **Solution:** Time large deductions with high-income years
• **Best Practice:** Maintain 2-3 year income and deduction forecasts

### **Inadequate **Carryforward Loss** Planning**
• **Problem:** Losing excess deductions due to poor planning
• **Solution:** Generate strategic excess for future high-income years
• **Best Practice:** Build deduction capacity 120-150% of current income

### **Insufficient Professional Coordination**
• **Problem:** Managing complex strategies without proper guidance
• **Solution:** Integrate tax strategist, CPA, and financial advisor
• **Best Practice:** Annual strategy review and adjustment sessions

## Measuring **Offset Stacking** Success

### **Tax Efficiency Metrics**
• **Effective Tax Rate:** Target under 15% on total income
• **Deduction Utilization Rate:** Optimize current vs. carryforward use
• **Strategy Diversification:** Maintain 3+ independent deduction sources

### **Wealth Building Indicators**
• **Asset Portfolio Growth:** Target 15-25% annual appreciation
• **Cash Flow Coverage:** Ensure positive cash flow across all investments
• **Risk-Adjusted Returns:** Balance tax benefits with investment returns

### **Strategic Positioning Goals**
• **Income Independence:** Build deduction capacity exceeding W-2 income
• **Flexibility Maintenance:** Preserve ability to adjust strategies
• **Long-Term Optimization:** Plan for changing income and tax scenarios

## Advanced Coordination Strategies

### **Income Timing Optimization**
• Coordinate equity compensation exercises with deduction availability
• Time asset sales to maximize deduction offset benefits
• Plan retirement account distributions around **offset stacking** capacity

### **Multi-State Tax Planning**
• Consider state tax implications of various deduction strategies
• Optimize domicile and asset location for maximum benefit
• Coordinate federal and state **carryforward loss** utilization

### **Estate and Succession Planning Integration**
• Build deduction strategies that enhance long-term wealth transfer
• Consider stepped-up basis opportunities
• Plan for charitable giving coordination with offset strategies

## What's Next: Entity Structure Optimization

Module 3 has introduced you to the power of **offset stacking** — systematically building multiple deduction sources that work together for maximum tax benefit. Helen's Year 2 example shows how sophisticated W-2 earners can eliminate tax liability on $370K+ of income while building substantial wealth.

In Module 4, we'll explore advanced entity structuring strategies that allow W-2 earners to optimize business structures, enhance deduction opportunities, and create additional layers of tax planning sophistication.

**Key Takeaway:** Single-strategy tax planning leaves money on the table. **Offset stacking** creates a comprehensive **deduction portfolio** that adapts to income changes while maximizing wealth building opportunities.

The most successful W-2 earners don't just find one good tax strategy — they build systematic approaches that stack multiple strategies for compounding benefits.

---

🎯 **Ready to test your offset stacking knowledge?** Take the Module 3 quiz to earn +50 XP and master these advanced coordination concepts before exploring Module 4's entity strategies.""",
                duration_minutes=55,
                order_index=3
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
        ),
        # W-2 Escape Plan Module 1 Questions (50 XP each, 3 questions)
        QuizQuestion(
            question="What is the primary disadvantage of W-2 income compared to other income types?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["It's taxed at lower rates", "It has limited deduction opportunities and no timing control", "It requires more paperwork", "It's subject to capital gains tax"],
            correct_answer="It has limited deduction opportunities and no timing control",
            explanation="W-2 income faces the highest effective tax rates with limited deduction opportunities, no control over timing, and immediate tax recognition through payroll withholding.",
            points=50,
            course_id=w2_course.id,
            module_id=1
        ),
        QuizQuestion(
            question="In Olivia's case study, what strategy helped her reduce her effective tax rate from 34% to 21%?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Maximizing 401(k) contributions", "Using QOF investment and STR depreciation to offset W-2 income", "Switching to contractor status", "Moving to a lower tax state"],
            correct_answer="Using QOF investment and STR depreciation to offset W-2 income",
            explanation="Olivia used RSU gains to fund a Qualified Opportunity Fund investment in short-term rental properties, then used the depreciation from those properties to offset her W-2 income through REPS qualification.",
            points=50,
            course_id=w2_course.id,
            module_id=1
        ),
        QuizQuestion(
            question="What is the key difference between forward-looking planning and traditional CPA approaches for W-2 earners?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Forward-looking planning costs more", "Forward-looking planning proactively structures additional income sources and deduction opportunities", "Traditional CPAs file earlier", "There is no significant difference"],
            correct_answer="Forward-looking planning proactively structures additional income sources and deduction opportunities",
            explanation="Forward-looking planning focuses on proactively creating structures and opportunities for tax optimization, while traditional CPA approaches typically focus on compliance and filing based on existing income and deductions.",
            points=50,
            course_id=w2_course.id,
            module_id=1
        ),
        # W-2 Escape Plan Module 2 Questions (50 XP each, 3 questions)
        QuizQuestion(
            question="What is the primary purpose of 'repositioning' already-taxed W-2 income?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["To avoid paying taxes on future income", "To transform passive income into active, tax-advantaged investments that generate ongoing deductions", "To convert W-2 income into business income", "To defer all current year taxes"],
            correct_answer="To transform passive income into active, tax-advantaged investments that generate ongoing deductions",
            explanation="Repositioning involves strategically deploying already-taxed W-2 income into investments and structures that generate immediate tax deductions, ongoing passive income, and long-term wealth building opportunities.",
            points=50,
            course_id=w2_course.id,
            module_id=2
        ),
        QuizQuestion(
            question="In Helen's case study, what was the key strategy that allowed her to eliminate her W-2 tax burden?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Using QOF to defer capital gains and STR depreciation to offset W-2 income", "Converting to contractor status", "Moving to a tax-free state", "Maximizing 401k contributions"],
            correct_answer="Using QOF to defer capital gains and STR depreciation to offset W-2 income",
            explanation="Helen used a Qualified Opportunity Fund to defer $183K in capital gains taxes, then invested in Short-Term Rental properties to generate $156K in depreciation losses that offset her $160K W-2 wages through material participation.",
            points=50,
            course_id=w2_course.id,
            module_id=2
        ),
        QuizQuestion(
            question="What is the key requirement to use Short-Term Rental depreciation losses against W-2 income?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Own more than 10 properties", "Material participation with 750+ documented hours annually", "Hire a property management company", "Live in one of the rental properties"],
            correct_answer="Material participation with 750+ documented hours annually",
            explanation="To use STR depreciation losses against W-2 income, you must qualify for material participation by spending 750+ hours annually in short-term rental activities and maintaining detailed documentation of these activities.",
            points=50,
            course_id=w2_course.id,
            module_id=2
        ),
        # W-2 Escape Plan Module 3 Questions (50 XP each, 3 questions)
        QuizQuestion(
            question="What is the primary benefit of 'offset stacking' compared to single-strategy tax planning?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["It's less risky than single strategies", "It systematically layers multiple deduction strategies for maximum tax benefit", "It requires less documentation", "It only works for high-income earners"],
            correct_answer="It systematically layers multiple deduction strategies for maximum tax benefit",
            explanation="Offset stacking strategically combines multiple tax deduction sources to maximize overall tax benefit, creating far more tax savings than any single strategy alone through synergistic layering.",
            points=50,
            course_id=w2_course.id,
            module_id=3
        ),
        QuizQuestion(
            question="In Helen's Year 2 case study, how did she eliminate taxes on $370K of income?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["Used only STR depreciation", "Combined STR depreciation ($223K) + Energy IDCs ($175K) + Equipment depreciation ($45K)", "Moved to a tax-free state", "Converted to contractor status"],
            correct_answer="Combined STR depreciation ($223K) + Energy IDCs ($175K) + Equipment depreciation ($45K)",
            explanation="Helen used offset stacking to combine $223K in STR depreciation, $175K in energy IDCs, and $45K in equipment depreciation for total deductions of $443K, which exceeded her $370K income and created a $73K carryforward loss.",
            points=50,
            course_id=w2_course.id,
            module_id=3
        ),
        QuizQuestion(
            question="What is the strategic purpose of generating 'carryforward losses' in offset stacking?",
            type=QuizQuestionType.MULTIPLE_CHOICE,
            options=["To reduce current year income only", "To create excess deductions that can offset future high-income years", "To avoid paying any taxes ever", "To qualify for government benefits"],
            correct_answer="To create excess deductions that can offset future high-income years",
            explanation="Carryforward losses are strategically generated to create a buffer of excess deductions that can be used to offset future income spikes, bonus years, or equity compensation, providing multi-year tax planning flexibility.",
            points=50,
            course_id=w2_course.id,
            module_id=3
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
            definition="Short-Term Rental (STR): A property rented for an average stay of 7 days or less, qualifying for different tax treatment under IRC §469 and Treas. Reg. §1.469-1T(e)(3).",
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
            term="Effective Tax Rate",
            definition="The percentage of total income that is actually paid in taxes, calculated by dividing total tax liability by total income. This provides a more accurate picture of tax burden than marginal tax rates.",
            category="Tax Terms",
            related_terms=["Tax Liability", "AGI", "W-2 Income", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Forward-Looking Planning",
            definition="Proactive tax strategy that focuses on structuring future income and investments to optimize tax outcomes, rather than simply reacting to past year tax liabilities.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "CPA vs Strategist", "Strategic Planning"]
        ),
        GlossaryTerm(
            term="Repositioning",
            definition="The strategic deployment of already-taxed income into investments and structures that generate immediate tax deductions, ongoing passive income, and long-term wealth building opportunities.",
            category="Tax Strategy",
            related_terms=["Tax Planning", "W-2 Income", "Capital Gain Deferral"]
        ),
        GlossaryTerm(
            term="Qualified Opportunity Fund (QOF)",
            definition="Investment vehicles designed to spur economic development in distressed communities. QOFs allow investors to defer capital gains taxes and potentially eliminate taxes on appreciation after 10 years.",
            category="Investment Strategy",
            related_terms=["Capital Gain Deferral", "Tax Planning", "Repositioning"]
        ),
        GlossaryTerm(
            term="Short-Term Rental (STR)",
            definition="Rental properties rented for periods of less than 30 days, typically managed like hotel accommodations. STRs offer higher income potential and enhanced depreciation benefits compared to traditional rentals.",
            category="Real Estate",
            related_terms=["Material Participation", "Bonus Depreciation", "Depreciation Loss"]
        ),
        GlossaryTerm(
            term="Bonus Depreciation",
            definition="Tax provision allowing businesses to immediately deduct 100% of the cost of qualifying business assets in the year they are purchased, rather than depreciating them over several years.",
            category="Tax Terms",
            related_terms=["Depreciation Loss", "Business Expenses", "Short-Term Rental (STR)"]
        ),
        GlossaryTerm(
            term="Material Participation",
            definition="IRS test requiring taxpayers to be involved in business operations on a regular, continuous, and substantial basis (typically 750+ hours for rental activities) to use losses against other income.",
            category="Tax Terms",
            related_terms=["Short-Term Rental (STR)", "Depreciation Loss", "Business Income"]
        ),
        GlossaryTerm(
            term="Depreciation Loss",
            definition="Tax losses generated from the depreciation of business assets that can be used to offset other income, effectively reducing overall tax liability.",
            category="Tax Terms",
            related_terms=["Material Participation", "Bonus Depreciation", "Business Expenses"]
        ),
        GlossaryTerm(
            term="Capital Gain Deferral",
            definition="Strategy to postpone paying taxes on capital gains by reinvesting proceeds into qualifying investments like Qualified Opportunity Funds or 1031 exchanges.",
            category="Tax Strategy",
            related_terms=["Qualified Opportunity Fund (QOF)", "Repositioning", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Offset Stacking",
            definition="The strategic combination of multiple tax deduction sources to maximize overall tax benefit. Rather than relying on a single deduction type, offset stacking builds portfolios of complementary strategies.",
            category="Tax Strategy",
            related_terms=["Depreciation Offset", "Deduction Portfolio", "Tax Planning"]
        ),
        GlossaryTerm(
            term="Depreciation Offset",
            definition="Tax strategy using depreciation deductions from business assets (primarily real estate) to offset ordinary income, effectively reducing overall tax liability.",
            category="Tax Strategy",
            related_terms=["Short-Term Rental (STR)", "Material Participation", "Offset Stacking"]
        ),
        GlossaryTerm(
            term="Intangible Drilling Costs (IDCs)",
            definition="Immediate tax deductions available for expenses related to oil and gas drilling operations, including labor, materials, and equipment used in drilling wells.",
            category="Investment Strategy",
            related_terms=["Offset Stacking", "Carryforward Loss", "Energy Investments"]
        ),
        GlossaryTerm(
            term="Carryforward Loss",
            definition="Tax losses that exceed current year income and can be carried forward to offset income in future tax years, providing ongoing tax planning opportunities.",
            category="Tax Terms",
            related_terms=["Offset Stacking", "Tax Planning", "Deduction Portfolio"]
        ),
        GlossaryTerm(
            term="Deduction Portfolio",
            definition="Strategic collection of diverse tax deduction sources designed to work together synergistically, providing comprehensive tax optimization and risk diversification.",
            category="Tax Strategy",
            related_terms=["Offset Stacking", "Tax Planning", "Depreciation Offset"]
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
    
    # Sample marketplace items
    marketplace_items = [
        MarketplaceItem(
            name="Advanced Tax Strategy Consultation",
            description="One-on-one consultation with a tax strategist to review your specific situation",
            price=497.00,
            category="Consultation",
            is_featured=True,
            image_url="https://images.unsplash.com/photo-1556761175-4b46a572b786?w=400"
        ),
        MarketplaceItem(
            name="Entity Structure Analysis",
            description="Comprehensive analysis of your current entity structure with optimization recommendations",
            price=297.00,
            category="Analysis",
            is_featured=False,
            image_url="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400"
        ),
        MarketplaceItem(
            name="Tax Planning Template Library",
            description="Access to 25+ proven tax planning templates and checklists",
            price=197.00,
            category="Templates",
            is_featured=True,
            image_url="https://images.unsplash.com/photo-1586953208448-b95a79798f07?w=400"
        )
    ]
    
    for item in marketplace_items:
        await db.marketplace.insert_one(item.dict())
    
    # Initialize default user XP
    default_xp = UserXP(user_id="default_user")
    await db.user_xp.insert_one(default_xp.dict())
    
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
