# 🤖 AI-Powered Resume Builder & ATS Optimization Agent

> **Assignment Submission** | AI Agent Development  
> Developed with Python, Streamlit, and OpenAI GPT

---

## 📋 Project Overview

A fully functional AI agent that helps users create ATS-optimized, professionally formatted resumes. Users can either upload an existing resume or manually enter their details to generate a polished, job-ready resume with AI enhancements.

---

## 🚀 Features

### ✅ Core Features (All Implemented)
| Feature | Status |
|---------|--------|
| Upload existing resume (PDF/DOCX) | ✅ Done |
| Manual data entry with structured form | ✅ Done |
| Resume parsing (PDF & DOCX) | ✅ Done |
| ATS Score calculation | ✅ Done |
| AI-based content enhancement | ✅ Done |
| Keyword optimization | ✅ Done |
| Multiple professional templates | ✅ Done |
| Word (.docx) generation | ✅ Done |
| PDF generation | ✅ Done |
| ATS score display (before & after) | ✅ Done |

### 🌟 Bonus Features (Implemented)
| Feature | Status |
|---------|--------|
| Comparison Mode (Before vs After) | ✅ Done |
| Score Improvement Tracker | ✅ Done |
| AI Feedback Chat (via enhancement options) | ✅ Done |
| Multiple template designs | ✅ Done |
| Progress tracker in sidebar | ✅ Done |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                     │
│                       (app.py)                           │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
   ┌────▼─────┐              ┌──────▼─────┐
   │  Resume  │              │   Manual   │
   │  Upload  │              │   Entry    │
   └────┬─────┘              └──────┬─────┘
        └──────────┬────────────────┘
                   │
         ┌─────────▼──────────┐
         │   Resume Parser     │
         │  (resume_parser.py) │
         │  • PDF Parsing      │
         │  • DOCX Parsing     │
         │  • Data Extraction  │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │    ATS Scorer       │
         │  (ats_scorer.py)   │
         │  • Keyword Analysis │
         │  • Section Scoring  │
         │  • Content Quality  │
         │  • Format Check     │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │    AI Enhancer      │
         │  (ai_enhancer.py)  │
         │  • OpenAI GPT-3.5  │
         │  • Summary Polish   │
         │  • Bullet Points    │
         │  • Skill Expansion  │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Resume Generator   │
         │(resume_generator.py)│
         │  • DOCX Generation  │
         │  • PDF Generation   │
         │  • 3 Templates      │
         └────────────────────┘
```

---

## 📂 File Structure

```
resume_builder/
│
├── app.py                    # Main Streamlit application (UI & flow)
├── resume_parser.py          # PDF/DOCX parsing engine
├── ats_scorer.py             # ATS compatibility scoring engine
├── ai_enhancer.py            # OpenAI GPT enhancement module
├── resume_generator.py       # DOCX & PDF resume generation
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API Key (for AI enhancement)

### Step 1: Clone/Download the project
```bash
# Place all files in a directory called resume_builder/
cd resume_builder
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the application
```bash
streamlit run app.py
```

### Step 4: Open in browser
The app will open automatically at `http://localhost:8501`

---

## 🔑 Configuration

### OpenAI API Key
1. Get your API key from [platform.openai.com](https://platform.openai.com)
2. Enter it in the sidebar of the application
3. The key is used for AI-powered resume enhancement

> **Note:** The app works without an API key (with fallback rule-based enhancement), but AI enhancement requires a valid OpenAI key.

---

## 📊 System Flow

### Step 1: Input
- **Option A:** Upload existing resume (PDF or DOCX) → Auto-parsed into structured fields
- **Option B:** Fill the manual entry form with personal info, education, experience, skills, projects

### Step 2: ATS Score Analysis
- The ATS Scorer analyzes your resume across 4 dimensions:
  - **Keyword Score** (30%): Technical skills, soft skills, power verbs
  - **Section Score** (25%): Completeness of all required sections
  - **Content Score** (25%): Quantified achievements, summary quality
  - **Format Score** (20%): Contact info, LinkedIn, word count
- Provides specific missing keywords and improvement suggestions

### Step 3: AI Enhancement
- OpenAI GPT-3.5-turbo enhances:
  - Professional summary → compelling 60-100 word statement
  - Work experience → quantified, action-verb-led bullets
  - Projects → impact-focused descriptions
  - Skills → expanded list with role-relevant additions
- Score recalculated after enhancement to show improvement

### Step 4: Template Selection
3 professional templates:
- **Classic Professional** (Blue/Navy) - Traditional corporate
- **Modern Minimalist** (Dark/Steel) - Tech/startup roles
- **Executive Bold** (Dark/Red) - Leadership/senior roles

### Step 5: Download
- Download polished **Word (.docx)** file for editing
- Download ready-to-submit **PDF** file

---

## 🛠️ Technical Implementation

### ATS Scoring Engine (`ats_scorer.py`)
Custom-built scoring system that evaluates:
- 40+ technical keywords from popular JD requirements
- 18 soft skill keywords
- 36 power action verbs
- Quantified achievement patterns (%, $, numbers)
- Job description keyword matching
- Resume structure completeness

### Resume Parser (`resume_parser.py`)
- **PDF:** Uses `pdfplumber` (primary) with `PyPDF2` fallback
- **DOCX:** Uses `python-docx`
- Smart section detection via header keyword matching
- Contact info extraction with regex patterns
- Handles various resume formats

### AI Enhancer (`ai_enhancer.py`)
- Uses `gpt-3.5-turbo` for cost-effective enhancement
- Separate prompts optimized for each section
- Graceful fallback to rule-based enhancement if API unavailable
- Context-aware: incorporates target role, experience level, job description

### Resume Generator (`resume_generator.py`)
- **DOCX:** `python-docx` with custom styles, colored headers, bullet formatting
- **PDF:** `reportlab` with custom paragraph styles, HR dividers, color themes
- 3 distinct visual templates with different color palettes
- ATS-friendly single-column layouts

---

## 🌐 Deployment

### Deploy on Render
1. Push code to GitHub
2. Create new Web Service on [render.com](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variable `OPENAI_API_KEY` (optional)

### Deploy on Streamlit Cloud
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub repo
4. Set main file: `app.py`
5. Add secrets for API keys

---

## 📈 Scoring Breakdown

| Score Range | Status | Color |
|------------|--------|-------|
| 70-100 | 🟢 Good - Ready to Submit | Green |
| 50-69 | 🟡 Average - Needs Improvement | Yellow |
| 0-49 | 🔴 Poor - Major Revision Needed | Red |

---

## 🔄 API Integrations

| Service | Purpose | Required |
|---------|---------|----------|
| OpenAI GPT-3.5-turbo | Content enhancement | Optional* |

*Without OpenAI key, rule-based enhancement is applied automatically

---

## 📝 Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| AI/ML | OpenAI GPT-3.5-turbo |
| PDF Parsing | pdfplumber, PyPDF2 |
| DOCX Parsing | python-docx |
| DOCX Generation | python-docx |
| PDF Generation | ReportLab |
| ATS Scoring | Custom Python engine |
| Language | Python 3.8+ |
| Deployment | Render / Streamlit Cloud |

---

## 👤 Author

**AI Resume Builder & ATS Optimization Agent**  
Assignment Submission | February 2026

---

## 📞 Submission Notes

- ✅ Fully functional AI agent
- ✅ Manual entry + file upload support  
- ✅ ATS scoring with detailed breakdown
- ✅ AI-based content enhancement (OpenAI GPT)
- ✅ 3 professional LaTeX-inspired templates
- ✅ DOCX + PDF download
- ✅ Before/After comparison mode
- ✅ Score improvement tracker
- ✅ Clean, professional UI
- ✅ Ready for Vercel/Render deployment
