# The Escape Blueprint Course

**Course Type:** Free Primer  
**Total Modules:** 4 of 5 (Module 5 TBD)  
**Total Duration:** 145 minutes  
**Total XP Available:** 120 XP (Quiz) + Glossary XP (5 XP per term)  

## Course Overview

"The Escape Blueprint" is the foundational free course in the IRS Escape Plan platform. It provides essential tax strategy education covering why most people overpay taxes, the 6 core levers of tax control, real-world case studies, and personal tax exposure assessment.

## Learning Progression

### Module 1: Foundation
- **Why You're Overpaying the IRS** - Mindset shift from filing to planning
- **Core Concepts:** IRS is not the enemy, CPAs vs Strategists, Proactive vs Overpaying
- **XP Available:** 10 XP

### Module 2: Framework  
- **The 6 Levers That Actually Shift Your Tax Outcome**
- **Core Levers:** Entity Type, Income Type, Timing, Asset Location, Deduction Strategy, Exit Planning
- **XP Available:** 20 XP

### Module 3: Application
- **Real Tax Case Studies That Shift Everything**
- **Case Studies:** Noah (Tech + RSUs), Jessica (S-Corp), Liam (W-2 + Real Estate)
- **XP Available:** 30 XP

### Module 4: Assessment
- **Mapping Your Tax Exposure**
- **Self-Assessment:** Income Analysis, Entity Review, Deduction Strategy, Risk Mapping
- **XP Available:** 40 XP

## Interactive Features

### XP System
- **Quiz XP:** 10 XP per module (based on order_index * 10)
- **Glossary XP:** 5 XP per new term viewed
- **Total Possible:** 120 XP from quizzes + up to 90 XP from glossary (18 terms)

### Glossary Integration
- **Module-Specific Terms:** 3-6 terms per module
- **Inline Popovers:** Bolded terms clickable in content
- **Related Terms:** Cross-linking between concepts
- **XP Rewards:** First-time viewing bonus

### Quiz System
- **Module-Specific Questions:** 3 questions per module
- **Question Types:** Multiple choice with detailed explanations
- **Immediate Feedback:** Correct/incorrect with learning reinforcement

## Technical Implementation

### Backend (FastAPI + MongoDB)
- **Course Management:** Lessons with order-based XP calculation
- **Quiz System:** Module-filtered questions with scoring
- **Glossary API:** Search and term lookup functionality
- **User Progress:** XP tracking and lesson completion

### Frontend (React + Tailwind)
- **Netflix-Style UI:** Professional course cards and navigation
- **Interactive Elements:** Glossary popovers, quiz interface, XP tracking
- **Responsive Design:** Mobile and desktop optimized
- **Brand Colors:** Navy blue (#0f172a) and emerald green (#10b981)

## Course Files Structure

```
/courses/escape-blueprint/
├── README.md                 # This overview
├── module-1.md              # Foundation module content
├── module-2.md              # Framework module content  
├── module-3.md              # Application module content
├── module-4.md              # Assessment module content
├── quiz-questions.json      # All quiz questions by module
└── glossary-terms.json      # All glossary terms with metadata
```

## Implementation Status

✅ **Module 1:** Complete with XP, quiz, and glossary integration  
✅ **Module 2:** Complete with 6 levers framework and interactive features  
✅ **Module 3:** Complete with real case studies and financial examples  
✅ **Module 4:** Complete with self-assessment framework and exposure mapping  
🔄 **Module 5:** To be developed (course completion and roadmap building)

## Platform Integration

This course serves as the entry point to the full IRS Escape Plan platform, introducing users to:
- **Tax Strategy Mindset:** From reactive filing to proactive planning
- **Strategic Framework:** The 6 levers that control all tax outcomes
- **Real-World Application:** Case studies with documented results
- **Personal Assessment:** Tools to identify individual optimization opportunities

The course prepares users for advanced courses (**W-2 Escape Plan** and **Business Owner Escape Plan**) and marketplace tools.
