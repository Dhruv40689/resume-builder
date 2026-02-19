"""
AI-Powered Resume Builder & ATS Optimization Agent
Main Streamlit Application - v4
"""

# ── Suppress ALL noisy library warnings before any imports ───────────────────
import warnings
import logging
import os
import sys

# Kill pdfminer FontBBox / font warnings (they use logging.warning internally)
for noisy in ("pdfminer", "pdfminer.pdffont", "pdfminer.pdfpage",
               "pdfminer.converter", "pdfminer.layout", "pdfminer.high_level"):
    logging.getLogger(noisy).setLevel(logging.ERROR)

# Kill pdfplumber wrapper warnings
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

# Kill Python warnings for common noisy patterns
warnings.filterwarnings("ignore")          # suppress everything at startup
os.environ["PYTHONWARNINGS"] = "ignore"    # also for subprocesses

import streamlit as st
import io

# Page configuration
st.set_page_config(
    page_title="AI Resume Builder & ATS Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #black; }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 12px; color: #ffffff !important;
        text-align: center; margin-bottom: 2rem;
    }
    .main-header h1, .main-header p { color: #ffffff !important; }

    .score-card {
        background: #ffffff; border-radius: 12px; padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center;
        border: 1px solid #e9ecef;
    }
    .score-card div { color: #333333 !important; }
    .score-high   { color: #28a745 !important; font-size: 2.8rem; font-weight: 800; }
    .score-medium { color: #e67e22 !important; font-size: 2.8rem; font-weight: 800; }
    .score-low    { color: #dc3545 !important; font-size: 2.8rem; font-weight: 800; }

    .section-header {
        background: #ffffff; padding: 1rem 1.2rem;
        border-left: 5px solid #667eea; border-radius: 0 8px 8px 0;
        margin: 1.5rem 0 1rem 0; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .section-header h2 { color: #2c3e50 !important; margin: 0; font-size: 1.3rem; }

    /* FIX: explicit dark text for tip/keyword boxes */
    .tip-box {
        background: #eaf4fe !important; border: 1px solid #b8daff !important;
        border-radius: 8px; padding: 0.7rem 1rem; margin: 0.4rem 0;
        color: #1a1a2e !important; font-size: 0.95rem; line-height: 1.5;
    }
    .tip-box strong { color: #1a1a2e !important; }

    .kw-box {
        background: #fff3f3 !important; border: 1px solid #f5c6cb !important;
        border-radius: 8px; padding: 0.5rem 1rem; margin: 0.3rem 0;
        color: #721c24 !important; font-size: 0.9rem; font-weight: 600;
    }

    /* FIX: explicit white background and dark text for comparison */
    .comparison-box {
        background: #ffffff !important; border: 1px solid #dee2e6;
        border-radius: 10px; padding: 1.2rem; min-height: 200px;
        max-height: 420px; overflow-y: auto; color: #2c3e50 !important;
        font-size: 0.95rem; line-height: 1.7; white-space: pre-wrap;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important; border: none !important;
        padding: 0.7rem 1.5rem !important; border-radius: 8px !important;
        font-weight: 700 !important; font-size: 1rem !important;
    }

    [data-testid="stMetricLabel"] { color: #555555 !important; }
    [data-testid="stMetricValue"] { color: #2c3e50 !important; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ─── Module imports ───────────────────────────────────────────────────────────
from resume_parser import ResumeParser
from ats_scorer import ATSScorer
from ai_enhancer import AIEnhancer
from resume_generator import ResumeGenerator

# ─── Session state init ───────────────────────────────────────────────────────
defaults = {
    'resume_data': {}, 'original_text': '',
    'original_summary_snapshot': '',   # stores summary at save-time for comparison
    'enhanced_data': {}, 'original_score': None, 'enhanced_score': None,
    'step': 1, 'api_key': '', 'magical_api_key': '', 'job_description': '',
    'generated': False, 'docx_bytes': None, 'resume_bytes': b'', 'resume_filename': 'resume.pdf',
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Resume Builder & ATS Optimizer</h1>
    <p style="font-size:1.1rem;margin:0;">Create ATS-optimized, professionally formatted resumes with AI</p>
</div>""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # OpenAI key
    api_key = st.text_input("🤖 OpenAI API Key", type="password",
                            value=st.session_state.api_key, placeholder="sk-...")
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ OpenAI Key set")
    else:
        st.info("ℹ️ Add OpenAI key for GPT enhancement. Works without it too.")

    st.markdown("---")
    st.markdown("📊 **ATS Scoring:** Built-in engine (keyword, content, format & section analysis)")

    st.markdown("---")
    st.markdown("## 📊 Progress")
    steps = ["📥 Input", "📊 ATS Score", "✨ Enhance", "📝 Generate", "⬇️ Download"]
    for i, s in enumerate(steps, 1):
        if i < st.session_state.step:
            st.markdown(f"✅ {s}")
        elif i == st.session_state.step:
            st.markdown(f"🔵 **{s}** ← You are here")
        else:
            st.markdown(f"⭕ {s}")

    st.markdown("---")
    if st.button("🔄 Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 – INPUT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h2>Step 1 — Input Your Resume</h2></div>', unsafe_allow_html=True)

input_method = st.radio("Choose Input Method:", ["📤 Upload Existing Resume", "✏️ Enter Details Manually"], horizontal=True)

# ── Upload branch ─────────────────────────────────────────────────────────────
if input_method == "📤 Upload Existing Resume":
    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

    if uploaded_file:
        with st.spinner("Parsing your resume…"):
            parser     = ResumeParser()
            file_bytes = uploaded_file.read()
            # store raw bytes for MagicalAPI
            st.session_state.resume_bytes    = file_bytes
            st.session_state.resume_filename = uploaded_file.name
            if uploaded_file.name.lower().endswith('.pdf'):
                parsed_data, raw_text = parser.parse_pdf(file_bytes)
            else:
                parsed_data, raw_text = parser.parse_docx(file_bytes)

        st.success("✅ Resume parsed! Review and edit below, then click **Save Parsed Data**.")

        with st.expander("📋 Parsed Resume Data — Review & Edit", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                name     = st.text_input("Full Name",        value=parsed_data.get("name", ""))
                email    = st.text_input("Email",             value=parsed_data.get("email", ""))
                phone    = st.text_input("Phone",             value=parsed_data.get("phone", ""))
            with col2:
                linkedin = st.text_input("LinkedIn",          value=parsed_data.get("linkedin", ""))
                location = st.text_input("Location",          value=parsed_data.get("location", ""))
                website  = st.text_input("Website/Portfolio", value=parsed_data.get("website", ""))

            summary    = st.text_area("Professional Summary",
                                      value=parsed_data.get("summary", ""),
                                      height=110,
                                      help="Tip: Write 3-4 sentences — this is shown in Before/After comparison")
            skills_str = st.text_area("Skills (comma-separated)",
                                      value=", ".join(parsed_data.get("skills", [])), height=80)
            experience = st.text_area("Work Experience",
                                      value=parsed_data.get("experience_text", ""), height=220)
            education  = st.text_area("Education",
                                      value=parsed_data.get("education_text", ""),  height=100)
            projects   = st.text_area("Projects & Achievements",
                                      value=parsed_data.get("projects_text", ""),   height=150)
            certs_str  = st.text_area("Certifications (one per line)",
                                      value="\n".join(parsed_data.get("certifications", [])), height=80)

            if st.button("💾 Save Parsed Data"):
                cert_list  = [c.strip() for c in certs_str.split("\n")  if c.strip()]
                skill_list = [s.strip() for s in skills_str.split(",") if s.strip()]

                st.session_state.resume_data = {
                    "name": name, "email": email, "phone": phone,
                    "linkedin": linkedin, "location": location, "website": website,
                    "summary": summary, "skills": skill_list, "certifications": cert_list,
                    "education_text": education, "experience_text": experience, "projects_text": projects,
                }
                st.session_state.original_text = raw_text
                # ← snapshot so comparison works even after enhancement
                st.session_state.original_summary_snapshot = (
                    summary.strip() if summary.strip()
                    else "(No summary found in uploaded resume — add one above for better ATS score)"
                )
                st.session_state.step = max(st.session_state.step, 2)
                st.success("✅ Data saved! Scroll down to calculate your ATS score.")

# ── Manual entry branch ───────────────────────────────────────────────────────
else:
    st.markdown("### 👤 Personal Information")
    c1, c2, c3 = st.columns(3)
    with c1:
        name  = st.text_input("Full Name *", placeholder="John Doe")
        email = st.text_input("Email *",     placeholder="john@example.com")
    with c2:
        phone    = st.text_input("Phone",    placeholder="+91 9876543210")
        linkedin = st.text_input("LinkedIn", placeholder="linkedin.com/in/johndoe")
    with c3:
        location = st.text_input("Location",        placeholder="Mumbai, India")
        website  = st.text_input("Website / GitHub", placeholder="github.com/johndoe")

    st.markdown("### 📝 Professional Summary")
    summary = st.text_area("Summary",
                           placeholder="Results-driven professional with 5+ years of experience in…", height=110)

    st.markdown("### 🎓 Education")
    education_entries = []
    num_edu = st.number_input("Number of Education Entries", 1, 5, 1)
    for i in range(num_edu):
        with st.expander(f"Education #{i+1}", expanded=(i == 0)):
            ec1, ec2 = st.columns(2)
            with ec1:
                degree      = st.text_input(f"Degree #{i+1}",      placeholder="B.Tech – Computer Science", key=f"deg_{i}")
                institution = st.text_input(f"Institution #{i+1}", placeholder="IIT Bombay",               key=f"inst_{i}")
            with ec2:
                grad_year = st.text_input(f"Year #{i+1}",     placeholder="2022",   key=f"gyear_{i}")
                gpa       = st.text_input(f"GPA / % #{i+1}", placeholder="8.5/10", key=f"gpa_{i}")
            education_entries.append({"degree": degree, "institution": institution, "year": grad_year, "gpa": gpa})

    st.markdown("### 💼 Work Experience")
    experience_entries = []
    num_exp = st.number_input("Number of Experience Entries", 0, 10, 1)
    for i in range(num_exp):
        with st.expander(f"Experience #{i+1}", expanded=(i == 0)):
            xc1, xc2 = st.columns(2)
            with xc1:
                job_title = st.text_input(f"Job Title #{i+1}", placeholder="Software Engineer", key=f"jt_{i}")
                company   = st.text_input(f"Company #{i+1}",   placeholder="Google",           key=f"comp_{i}")
            with xc2:
                duration     = st.text_input(f"Duration #{i+1}", placeholder="Jan 2022 – Present", key=f"dur_{i}")
                job_location = st.text_input(f"Location #{i+1}", placeholder="Bengaluru, India",   key=f"jloc_{i}")
            responsibilities = st.text_area(
                f"Responsibilities & Achievements #{i+1}",
                placeholder="• Developed REST APIs\n• Reduced latency by 40%", height=120, key=f"resp_{i}")
            experience_entries.append({
                "title": job_title, "company": company, "duration": duration,
                "location": job_location, "responsibilities": responsibilities
            })

    st.markdown("### 🛠️ Skills & Certifications")
    sc1, sc2 = st.columns(2)
    with sc1:
        technical_skills = st.text_area("Technical Skills (comma-separated)",
                                        placeholder="Python, React, AWS, Docker", height=80)
        soft_skills      = st.text_area("Soft Skills",
                                        placeholder="Leadership, Communication", height=60)
    with sc2:
        certifications = st.text_area("Certifications (one per line)",
                                      placeholder="AWS Certified Developer\nGoogle ML Engineer", height=80)
        languages      = st.text_input("Languages", placeholder="English (Fluent), Hindi (Native)")

    st.markdown("### 🚀 Projects & Achievements")
    project_entries = []
    num_proj = st.number_input("Number of Projects", 0, 10, 1)
    for i in range(num_proj):
        with st.expander(f"Project #{i+1}", expanded=(i == 0)):
            pc1, pc2 = st.columns(2)
            with pc1:
                proj_name = st.text_input(f"Project Name #{i+1}", key=f"pname_{i}")
                proj_tech = st.text_input(f"Technologies #{i+1}",  placeholder="Python, React", key=f"ptech_{i}")
            with pc2:
                proj_link     = st.text_input(f"Link #{i+1}",     placeholder="github.com/…", key=f"plink_{i}")
                proj_duration = st.text_input(f"Duration #{i+1}", placeholder="3 months",     key=f"pdur_{i}")
            proj_desc = st.text_area(f"Description #{i+1}", height=100, key=f"pdesc_{i}")
            project_entries.append({
                "name": proj_name, "tech": proj_tech,
                "link": proj_link, "duration": proj_duration, "description": proj_desc
            })

    if st.button("💾 Save Resume Data"):
        all_skills = []
        if technical_skills:
            all_skills += [s.strip() for s in technical_skills.split(",") if s.strip()]
        if soft_skills:
            all_skills += [s.strip() for s in soft_skills.split(",") if s.strip()]

        edu_parts, exp_parts, proj_parts = [], [], []
        for edu in education_entries:
            if edu['degree']:
                p = edu['degree']
                if edu['institution']: p += f" | {edu['institution']}"
                if edu['year']:        p += f" | {edu['year']}"
                if edu['gpa']:         p += f" | GPA {edu['gpa']}"
                edu_parts.append(p)
        for exp in experience_entries:
            if exp['title']:
                p = f"{exp['title']} at {exp['company']} ({exp['duration']})"
                if exp['responsibilities']: p += f"\n{exp['responsibilities']}"
                exp_parts.append(p)
        for proj in project_entries:
            if proj['name']:
                p = proj['name']
                if proj['tech']:        p += f" | Tech: {proj['tech']}"
                if proj['description']: p += f"\n{proj['description']}"
                proj_parts.append(p)

        cert_list = [c.strip() for c in certifications.split("\n") if c.strip()] if certifications else []

        st.session_state.resume_data = {
            "name": name, "email": email, "phone": phone,
            "linkedin": linkedin, "location": location, "website": website,
            "summary": summary, "skills": all_skills, "certifications": cert_list,
            "languages": languages,
            "education_entries": education_entries, "experience_entries": experience_entries,
            "project_entries": project_entries,
            "education_text":  "\n".join(edu_parts),
            "experience_text": "\n\n".join(exp_parts),
            "projects_text":   "\n\n".join(proj_parts),
        }
        raw = (f"{name}\n{summary}\n" + " ".join(all_skills) + "\n" +
               "\n".join(edu_parts) + "\n" + "\n".join(exp_parts) + "\n" + "\n".join(proj_parts))
        st.session_state.original_text = raw
        st.session_state.original_summary_snapshot = (
            summary.strip() if summary.strip() else "(No summary entered — add one for a better ATS score)"
        )
        st.session_state.step = max(st.session_state.step, 2)
        st.success("✅ Resume data saved! Scroll down to calculate your ATS score.")

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 – ATS SCORING
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h2>Step 2 — ATS Score Analysis</h2></div>', unsafe_allow_html=True)

st.session_state.job_description = st.text_area(
    "📋 Target Job Description (optional — improves keyword matching)",
    value=st.session_state.job_description,
    placeholder="Paste the job description here for more accurate ATS scoring…",
    height=140
)

if st.button("📊 Calculate ATS Score", disabled=not bool(st.session_state.resume_data)):
    with st.spinner("Analysing your resume for ATS compatibility…"):
        scorer = ATSScorer(magical_api_key=st.session_state.magical_api_key)
        result = scorer.calculate_score(
            st.session_state.resume_data,
            st.session_state.original_text,
            st.session_state.job_description,
            resume_bytes=st.session_state.resume_bytes,
            resume_filename=st.session_state.resume_filename,
        )
        st.session_state.original_score = result
        st.session_state.step = max(st.session_state.step, 3)
    st.success("✅ ATS analysis complete!")

if st.session_state.original_score:
    score   = st.session_state.original_score
    overall = score['overall_score']

    st.markdown("#### 📊 ATS Analysis Results")
    c1, c2, c3, c4 = st.columns(4)

    def _score_card(col, value, label, colour):
        col.markdown(f"""
        <div class="score-card">
            <div style="font-size:2.6rem;font-weight:800;color:{colour};">{value}</div>
            <div style="font-size:0.95rem;color:#6c757d;margin-top:4px;">{label}</div>
        </div>""", unsafe_allow_html=True)

    oc = "#28a745" if overall >= 70 else "#e67e22" if overall >= 50 else "#dc3545"
    _score_card(c1, overall,               "Overall ATS Score", oc)
    _score_card(c2, score['keyword_score'],"Keyword Match",     "#17a2b8")
    _score_card(c3, score['format_score'], "Format Score",      "#6f42c1")
    _score_card(c4, score['content_score'],"Content Score",     "#fd7e14")

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### ❌ Missing Keywords")
        if score['missing_keywords']:
            for kw in score['missing_keywords'][:10]:
                st.markdown(f'<div class="kw-box">❌ &nbsp;{kw}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No critical keywords missing!")

    with col_right:
        st.markdown("#### 💡 Improvement Suggestions")
        for tip in score['suggestions']:
            st.markdown(f'<div class="tip-box">💡 &nbsp;{tip}</div>', unsafe_allow_html=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 – AI ENHANCEMENT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h2>Step 3 — AI-Powered Enhancement</h2></div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    target_role = st.text_input("🎯 Target Job Role", placeholder="Software Engineer, Data Scientist…")
with col_b:
    experience_level = st.selectbox("📈 Experience Level",
        ["Entry Level (0-2 years)", "Mid Level (2-5 years)", "Senior Level (5+ years)", "Executive Level"])

enhance_options = st.multiselect(
    "✨ Enhancement Options",
    ["Improve Professional Tone", "Optimize Keywords", "Quantify Achievements",
     "Enhance Summary", "Improve Action Verbs", "Fix Grammar & Clarity"],
    default=["Improve Professional Tone", "Optimize Keywords", "Enhance Summary", "Improve Action Verbs"]
)

if not st.session_state.api_key:
    st.info("ℹ️ No OpenAI key — rule-based enhancement will run automatically. Add a key for GPT-powered results.")

if st.button("🚀 Enhance Resume", disabled=not bool(st.session_state.resume_data)):
    with st.spinner("🤖 Enhancing your resume… please wait…"):
        bar = st.progress(10)
        enhancer = AIEnhancer(st.session_state.api_key)
        bar.progress(30)
        enhanced = enhancer.enhance_resume(
            st.session_state.resume_data,
            st.session_state.job_description,
            target_role, experience_level, enhance_options
        )
        bar.progress(70)

        # ── FIX: merge ALL original fields so enhanced data is always complete ──
        for k, v in st.session_state.resume_data.items():
            if k not in enhanced or not enhanced[k]:
                enhanced[k] = v

        st.session_state.enhanced_data = enhanced

        # ── FIX: score with original + enhanced combined text to avoid regression ──
        scorer = ATSScorer(magical_api_key=st.session_state.magical_api_key)
        combined_text = st.session_state.original_text + " " + enhanced.get('full_text', '')
        enhanced_score = scorer.calculate_score(
            enhanced, combined_text, st.session_state.job_description,
            resume_bytes=st.session_state.resume_bytes,
            resume_filename=st.session_state.resume_filename,
        )
        st.session_state.enhanced_score = enhanced_score
        bar.progress(100)
        st.session_state.step = max(st.session_state.step, 4)
    st.success("✅ Resume enhanced successfully!")

# ── Score tracker + Before/After ─────────────────────────────────────────────
if st.session_state.enhanced_data:
    if st.session_state.original_score and st.session_state.enhanced_score:
        orig_s = st.session_state.original_score['overall_score']
        enh_s  = st.session_state.enhanced_score['overall_score']
        delta  = enh_s - orig_s

        st.markdown("### 📊 Score Improvement Tracker")
        m1, m2, m3 = st.columns(3)
        m1.metric("Original Score", f"{orig_s}/100")
        m2.metric("Enhanced Score", f"{enh_s}/100",
                  delta=f"+{delta} pts" if delta >= 0 else f"{delta} pts")
        m3.metric("Improvement",    f"{delta} pts",
                  delta="🎉 Great!" if delta > 10 else ("✅ Improved" if delta >= 0 else "⚠️ Check content"))

    st.markdown("### 🔍 Before vs After Comparison")

    # ── FIX: always use snapshot for original, never live resume_data ──
    orig_sum = (st.session_state.original_summary_snapshot or
                st.session_state.resume_data.get("summary", "") or
                "(No summary in original resume — add one for a better ATS score)")
    enh_sum  = (st.session_state.enhanced_data.get("summary", "") or
                "(Enhancement did not produce a summary)")

    co, ce = st.columns(2)
    with co:
        st.markdown("**📄 Original Summary**")
        st.markdown(f'<div class="comparison-box">{orig_sum}</div>', unsafe_allow_html=True)
    with ce:
        st.markdown("**✨ Enhanced Summary**")
        st.markdown(f'<div class="comparison-box">{enh_sum}</div>', unsafe_allow_html=True)

    orig_exp = st.session_state.resume_data.get("experience_text", "")
    enh_exp  = st.session_state.enhanced_data.get("experience_text", orig_exp)
    if orig_exp or enh_exp:
        st.markdown("**💼 Work Experience — Before vs After**")
        xe1, xe2 = st.columns(2)
        with xe1:
            st.markdown(f'<div class="comparison-box">{orig_exp or "(empty)"}</div>', unsafe_allow_html=True)
        with xe2:
            st.markdown(f'<div class="comparison-box">{enh_exp or "(empty)"}</div>', unsafe_allow_html=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 – TEMPLATE SELECTION
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h2>Step 4 — Choose Template</h2></div>', unsafe_allow_html=True)

t1, t2, t3 = st.columns(3)
tmpl_defs = [
    ("Classic Professional", "#667eea", "📋",
     "Traditional layout — great for corporate & government roles",
     "✅ ATS Friendly &nbsp;|&nbsp; ✅ Clean &nbsp;|&nbsp; ✅ Widely Accepted"),
    ("Modern Minimalist",    "#28a745", "🎯",
     "Clean, modern design for tech & startup roles",
     "✅ ATS Friendly &nbsp;|&nbsp; ✅ Modern &nbsp;|&nbsp; ✅ Skills-Focused"),
    ("Executive Bold",       "#e67e22", "⚡",
     "Bold design for senior, leadership & executive roles",
     "✅ ATS Friendly &nbsp;|&nbsp; ✅ Leadership &nbsp;|&nbsp; ✅ Impact-Driven"),
]
for col, (tname, border, icon, desc, tags) in zip([t1, t2, t3], tmpl_defs):
    col.markdown(f"""
    <div style="border:2px solid {border};border-radius:12px;padding:1.2rem;
                text-align:center;background:#fff;min-height:200px;">
        <div style="font-size:2.5rem;">{icon}</div>
        <strong style="color:#2c3e50;">{tname}</strong>
        <p style="color:#555;font-size:0.88rem;margin:6px 0;">{desc}</p>
        <p style="color:#666;font-size:0.82rem;">{tags}</p>
    </div>""", unsafe_allow_html=True)

selected_template = st.selectbox(
    "✅ Confirm your template choice:",
    ["Classic Professional", "Modern Minimalist", "Executive Bold"]
)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 – GENERATE & DOWNLOAD
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><h2>Step 5 — Generate & Download</h2></div>', unsafe_allow_html=True)

if st.button("⚡ Generate Resume Now", type="primary"):
    final_data = st.session_state.enhanced_data if st.session_state.enhanced_data else st.session_state.resume_data
    if not final_data:
        st.error("Please complete and save your resume data first!")
    else:
        with st.spinner("Building your professional resume…"):
            try:
                gen = ResumeGenerator()
                st.session_state.docx_bytes = gen.generate_docx(final_data, selected_template)
                st.session_state.generated  = True
                st.session_state.step       = 5
            except Exception as e:
                import traceback
                st.error(f"Generation error: {e}")
                st.code(traceback.format_exc())

if st.session_state.generated and st.session_state.docx_bytes:
    st.success("🎉 Your optimized resume is ready to download!")

    final_data = st.session_state.enhanced_data if st.session_state.enhanced_data else st.session_state.resume_data
    name_slug  = final_data.get('name', 'Resume').replace(' ', '_')

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "⬇️ Download Word (.docx)", data=st.session_state.docx_bytes,
            file_name=f"{name_slug}_Optimized_Resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with dl2:
        try:
            gen = ResumeGenerator()
            pdf_bytes = gen.generate_pdf(final_data, selected_template)
            st.download_button(
                "⬇️ Download PDF", data=pdf_bytes,
                file_name=f"{name_slug}_Optimized_Resume.pdf",
                mime="application/pdf", use_container_width=True
            )
        except Exception as e:
            st.warning(f"PDF note: {e}")

    # Final ATS score banner
    score_obj   = st.session_state.enhanced_score or st.session_state.original_score
    if score_obj:
        fs  = score_obj['overall_score']
        em  = "🟢" if fs >= 70 else "🟡" if fs >= 50 else "🔴"
        col = "#28a745" if fs >= 70 else "#e67e22" if fs >= 50 else "#dc3545"
        st.markdown(f"""
        <div style="text-align:center;padding:2rem;
                    background:linear-gradient(135deg,#667eea18,#764ba218);
                    border-radius:14px;border:1px solid #dee2e6;margin-top:1.5rem;">
            <div style="font-size:3.5rem;">{em}</div>
            <div style="font-size:3rem;font-weight:800;color:{col};">{fs}/100</div>
            <div style="font-size:1.1rem;color:#495057;margin-top:4px;">Final Optimized ATS Score</div>
        </div>""", unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#6c757d;padding:1rem;">
    <p>🤖 AI Resume Builder & ATS Optimizer | Powered by OpenAI GPT | Built with Streamlit</p>
    <p style="font-size:0.8rem;">Tip: Tailor your resume for each job application for best results.</p>
</div>""", unsafe_allow_html=True)