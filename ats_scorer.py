import re
import io
import json
import requests
import tempfile
import os
from typing import Dict, List, Tuple, Optional


class MagicalAPIClient:

    BASE = "https://api.magicalapi.com"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def review_resume(self, resume_bytes: bytes, filename: str = "resume.pdf") -> dict:
        url = f"{self.BASE}/resume/en/v1/review"
        files = {"resume": (filename, resume_bytes, self._mime(filename))}
        try:
            resp = requests.post(url, headers=self.headers, files=files, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[MagicalAPI review error] {e}")
            return {}

    def score_resume(self, resume_bytes: bytes, job_description: str,
                     filename: str = "resume.pdf") -> dict:
        url = f"{self.BASE}/resume/en/v1/score"
        files = {"resume": (filename, resume_bytes, self._mime(filename))}
        data = {"job_description": job_description}
        try:
            resp = requests.post(url, headers=self.headers, files=files,
                                 data=data, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[MagicalAPI score error] {e}")
            return {}

    @staticmethod
    def _mime(filename: str) -> str:
        return ("application/pdf" if filename.lower().endswith(".pdf")
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


def _parse_magical_review(resp: dict) -> Optional[dict]:
    try:
        data = resp.get("data") or resp
        overall = int(data.get("score", 0))
        if overall == 0:
            return None

        sections = data.get("sections", {})
        suggestions = data.get("suggestions", [])
        missing_kw = data.get("missing_keywords", [])

        for sec_name, sec_data in sections.items():
            if isinstance(sec_data, dict):
                for con in sec_data.get("cons", []):
                    if con and con not in suggestions:
                        suggestions.append(con)

        def sec(key, default=0):
            s = sections.get(key, {})
            return int(s.get("score", default)) if isinstance(s, dict) else default

        return {
            "overall_score": overall,
            "keyword_score": sec("skills", overall),
            "format_score": sec("contact", overall),
            "content_score": sec("experience", overall),
            "section_score": sec("summary", overall),
            "suggestions": [str(s) for s in suggestions if s][:8],
            "missing_keywords": [str(k) for k in missing_kw][:15],
            "power_verb_count": 0,
            "quantified_achievements": 0,
            "source": "MagicalAPI",
        }
    except Exception as e:
        print(f"[parse_magical_review error] {e}")
        return None


def _parse_magical_score(resp: dict) -> Optional[int]:
    try:
        data = resp.get("data") or resp
        return int(data.get("score", 0)) or None
    except Exception:
        return None


class _BuiltinScorer:
    TECHNICAL_KEYWORDS = [
        'python', 'javascript', 'java', 'c++', 'c#', 'react', 'angular', 'vue', 'node.js',
        'django', 'flask', 'spring', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'sql', 'postgresql',
        'mongodb', 'redis', 'git', 'github', 'ci/cd', 'agile', 'scrum', 'devops',
        'html', 'css', 'typescript', 'graphql', 'rest api', 'microservices', 'linux',
        'data science', 'artificial intelligence', 'nlp', 'computer vision', 'blockchain',
        'generative ai', 'llm', 'langchain', 'hugging face', 'fastapi', 'streamlit',
        'flutter', 'android', 'reinforcement learning', 'transformers', 'bert',
        'fine-tuning', 'rag', 'crewai', 'mlflow', 'oracle',
    ]

    SOFT_SKILLS = [
        'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
        'project management', 'critical thinking', 'collaboration', 'adaptable',
        'organized', 'detail-oriented', 'self-motivated', 'innovative', 'strategic',
        'mentoring', 'coaching',
    ]

    POWER_VERBS = [
        'achieved', 'improved', 'reduced', 'increased', 'developed', 'launched',
        'managed', 'led', 'created', 'built', 'designed', 'implemented', 'delivered',
        'optimized', 'streamlined', 'automated', 'collaborated', 'mentored', 'trained',
        'analyzed', 'evaluated', 'generated', 'enhanced', 'accelerated', 'drove',
        'established', 'spearheaded', 'orchestrated', 'transformed', 'scaled',
    ]

    QUANTIFIERS = [
        r'\d+%', r'\$\d+', r'\d+x', r'\d+\+',
        r'\d+ (percent|million|billion|thousand)',
        r'(increased|decreased|reduced|improved).*\d+',
    ]

    def calculate(self, data: dict, raw_text: str, job_description: str = "") -> dict:
        full = self._full_text(data, raw_text)
        full_lower = full.lower()

        sec_s, sec_sg = self._sections(data)
        kw_s, kw_sg, missing = self._keywords(full_lower, job_description)
        con_s, con_sg = self._content(full_lower, data)
        fmt_s, fmt_sg = self._format(data, full)

        overall = sec_s*0.25 + kw_s*0.30 + con_s*0.25 + fmt_s*0.20
        if job_description:
            overall = min(100, overall + self._jd_match(full_lower, job_description)*10)

        suggestions = (sec_sg + kw_sg + con_sg + fmt_sg)[:8]
        return {
            "overall_score": round(overall),
            "keyword_score": round(kw_s),
            "format_score": round(fmt_s),
            "content_score": round(con_s),
            "section_score": round(sec_s),
            "suggestions": suggestions,
            "missing_keywords": missing[:15],
            "power_verb_count": sum(1 for v in self.POWER_VERBS if v in full_lower),
            "quantified_achievements": sum(len(re.findall(p, full, re.I)) for p in self.QUANTIFIERS),
            "source": "Built-in",
        }

    def _full_text(self, data, raw):
        parts = [raw or ""]
        for k in ['summary','experience_text','education_text','projects_text']:
            if data.get(k): parts.append(str(data[k]))
        if data.get('skills'): parts.append(' '.join(data['skills']))
        if data.get('certifications'): parts.append(' '.join(data['certifications']))
        for e in data.get('experience_entries', []):
            for f in ['title','company','responsibilities']:
                if e.get(f): parts.append(str(e[f]))
        for e in data.get('project_entries', []):
            for f in ['name','tech','description']:
                if e.get(f): parts.append(str(e[f]))
        return ' '.join(parts)

    def _has(self, data, *keys):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list) and any(
                (isinstance(i,dict) and any(i.values())) or (isinstance(i,str) and i.strip())
                for i in v): return True
            if isinstance(v, str) and v.strip(): return True
        return False

    def _sections(self, data):
        score, sg = 0, []
        for keys, pts, msg in [
            (['name'], 10, "Add your full name"),
            (['email'], 10, "Add a professional email"),
            (['phone'], 8, "Add your phone number"),
            (['summary'], 15, "Add a professional summary"),
            (['skills'], 20, "Add a dedicated skills section"),
            (['experience_text','experience_entries'], 20, "Add work experience"),
            (['education_text', 'education_entries'], 17, "Add your education"),
        ]:
            if self._has(data, *keys): score += pts
            else: sg.append(msg)
        return min(100, score), sg

    def _keywords(self, text, jd):
        score, sg, missing = 0, [], []
        found_tech = [k for k in self.TECHNICAL_KEYWORDS if k in text]
        score += min(50, len(found_tech)/len(self.TECHNICAL_KEYWORDS)*100)
        if len(found_tech) < 5: sg.append("Add more technical skills relevant to your role")

        found_soft = [k for k in self.SOFT_SKILLS if k in text]
        score += min(20, len(found_soft)/len(self.SOFT_SKILLS)*100)
        if len(found_soft) < 3: sg.append("Include soft skills like leadership and communication")

        found_verbs = [v for v in self.POWER_VERBS if v in text]
        score += min(30, len(found_verbs)/len(self.POWER_VERBS)*100)
        if len(found_verbs) < 5:
            sg.append("Use strong action verbs: achieved, led, implemented, optimized")
            missing += ['achieved', 'led', 'implemented', 'optimized', 'developed']

        if jd:
            jd_kws = self._jd_kws(jd)
            miss = [k for k in jd_kws if k.lower() not in text]
            missing += miss[:10]
            if len(miss)/max(len(jd_kws),1) > 0.5:
                sg.append(f"Add job-description keywords: {', '.join(miss[:5])}")

        return min(100, score), sg, missing

    def _content(self, text, data):
        score, sg = 0, []
        qc = sum(len(re.findall(p, text, re.I)) for p in self.QUANTIFIERS)
        if qc >= 5: score += 30
        elif qc >= 3: score += 20; sg.append("Add more quantified achievements (%, $, numbers)")
        elif qc >= 1: score += 10; sg.append("Quantify achievements with metrics")
        else: sg.append("Add specific numbers to your achievements")

        s = data.get('summary','')
        if len(s)>100: score += 20
        elif len(s)>50: score += 10; sg.append("Expand your summary to 3-4 sentences")
        else: sg.append("Write a compelling 3-4 sentence professional summary")

        skills = data.get('skills',[])
        if len(skills)>=10: score += 25
        elif len(skills)>=5: score += 15; sg.append("Add more skills to strengthen your profile")
        else: score += 5; sg.append("List at least 10 relevant skills")

        vc = sum(1 for v in self.POWER_VERBS if v in text)
        if vc>=8: score += 25
        elif vc>=5: score += 15
        elif vc>=2: score += 8
        else: sg.append("Start bullet points with strong action verbs")

        return min(100, score), sg

    def _format(self, data, full):
        score, sg = 60, []
        mc = [f for f in ['name','email','phone'] if not data.get(f)]
        if mc: score -= 10*len(mc); sg.append(f"Missing contact info: {', '.join(mc)}")
        else: score += 15
        if data.get('linkedin'): score += 10
        else: sg.append("Add your LinkedIn profile URL")
        wc = len(full.split())
        if 300<=wc<=900: score += 15
        elif wc < 300: score -= 10; sg.append("Resume too short — add more detail")
        return min(100, max(0,score)), sg

    def _jd_kws(self, jd):
        jd_l = jd.lower()
        kws = [k for k in self.TECHNICAL_KEYWORDS if k in jd_l]
        skip = {'The','This','That','With','Will','Must','Have','Your','Our','We',
                'You','Are','For','And','Not','Any','All','Can','Would','Should',
                'Could','Team','Work','Help','Role','Job','Years','Strong','Good'}
        for w in re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', jd):
            if w not in skip and w not in kws: kws.append(w)
        return list(set(kws))

    def _jd_match(self, text, jd):
        kws = self._jd_kws(jd)
        if not kws: return 0
        return sum(1 for k in kws if k.lower() in text)/len(kws)


class ATSScorer:

    def __init__(self, magical_api_key: str = ""):
        self.magical_key = magical_api_key.strip()
        self._builtin = _BuiltinScorer()

    def calculate_score(
        self,
        resume_data: dict,
        raw_text: str,
        job_description: str = "",
        resume_bytes: bytes = b"",
        resume_filename: str = "resume.pdf",
    ) -> dict:

        builtin_result = self._builtin.calculate(resume_data, raw_text, job_description)

        if not self.magical_key:
            return builtin_result

        client = MagicalAPIClient(self.magical_key)
        magical_result = None
        job_match_score = None

        if resume_bytes:
            review_resp = client.review_resume(resume_bytes, resume_filename)
            magical_result = _parse_magical_review(review_resp)

            if job_description:
                score_resp = client.score_resume(resume_bytes, job_description, resume_filename)
                job_match_score = _parse_magical_score(score_resp)
        else:
            try:
                text_bytes = self._resume_to_text_bytes(resume_data, raw_text)
                review_resp = client.review_resume(text_bytes, "resume.txt")
                magical_result = _parse_magical_review(review_resp)
                if job_description:
                    score_resp = client.score_resume(text_bytes, job_description, "resume.txt")
                    job_match_score = _parse_magical_score(score_resp)
            except Exception as e:
                print(f"[MagicalAPI fallback text error] {e}")

        if magical_result:
            merged = dict(magical_result)

            for k in ('keyword_score','format_score','content_score','section_score'):
                if not merged.get(k):
                    merged[k] = builtin_result.get(k, 0)

            merged['builtin_score'] = builtin_result['overall_score']
            merged['magical_score'] = magical_result['overall_score']

            if job_match_score:
                merged['job_match_score'] = job_match_score

            return merged
        else:
            result = dict(builtin_result)
            result['source'] = 'Built-in (MagicalAPI unavailable)'
            return result

    @staticmethod
    def _resume_to_text_bytes(resume_data: dict, raw_text: str) -> bytes:
        parts = []
        for k in ['name','email','phone','linkedin','location','summary']:
            if resume_data.get(k): parts.append(str(resume_data[k]))
        if resume_data.get('skills'):
            parts.append("Skills: " + ", ".join(resume_data['skills']))
        for k in ['experience_text','education_text','projects_text']:
            if resume_data.get(k): parts.append(str(resume_data[k]))
        return '\n'.join(parts).encode('utf-8') or raw_text.encode('utf-8')