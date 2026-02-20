"""
AI Enhancement Module - v4
- Fail-fast on GPT 429 (quota exceeded): logs once, immediately falls back
- Never retries quota errors
- Rule-based path ALWAYS rewrites content (not just when empty)
"""

import re
from typing import Dict, List


class AIEnhancer:

    def __init__(self, api_key: str):
        self.api_key   = (api_key or "").strip()
        self.available = False
        self.client    = None
        self._quota_exceeded = False  # set True on first 429 → no more calls

        if self.api_key.startswith('sk-'):
            try:
                from openai import OpenAI
                self.client    = OpenAI(api_key=self.api_key)
                self.available = True
            except ImportError:
                pass

    # ── Public ────────────────────────────────────────────────────────────────

    def enhance_resume(
        self,
        resume_data:      Dict,
        job_description:  str       = "",
        target_role:      str       = "",
        experience_level: str       = "Entry Level",
        enhance_options:  List[str] = None,
    ) -> Dict:

        if self.available and not self._quota_exceeded:
            try:
                result = self._gpt_enhance(
                    resume_data, job_description, target_role,
                    experience_level, enhance_options or []
                )
                if result and self._is_improved(result, resume_data):
                    result['full_text'] = self._build_full_text(result)
                    return result
            except Exception as e:
                print(f"[AIEnhancer] GPT failed, using rule-based: {e}")

        return self._rule_enhance(resume_data, target_role, job_description)

    # ── GPT path ──────────────────────────────────────────────────────────────

    def _gpt_enhance(self, data, jd, role, level, options):
        enhanced = dict(data)
        ctx = self._ctx(jd, role, level)

        enhanced['summary'] = self._call(self._summary_prompt(data.get('summary',''), ctx), 220) or data.get('summary','')

        if data.get('experience_text'):
            r = self._call(self._experience_prompt(data['experience_text'], ctx), 900)
            enhanced['experience_text'] = r or data['experience_text']

        if data.get('experience_entries'):
            new_entries = []
            for exp in data['experience_entries']:
                e = dict(exp)
                resp_text = '\n'.join(exp.get('responsibilities', []))
                if resp_text:
                    r = self._call(self._bullets_prompt(resp_text, ctx), 400)
                    e['responsibilities'] = (r or resp_text).split('\n')
                new_entries.append(e)
            enhanced['experience_entries'] = new_entries

        if data.get('projects_text'):
            r = self._call(self._projects_prompt(data['projects_text'], ctx), 600)
            enhanced['projects_text'] = r or data['projects_text']

        if data.get('skills'):
            r = self._call(self._skills_prompt(data['skills'], jd, role), 200)
            if r:
                new_skills = [s.strip() for s in r.split(',') if s.strip()]
                enhanced['skills'] = list(dict.fromkeys(data['skills'] + new_skills))[:25]

        enhanced['full_text'] = self._build_full_text(enhanced)
        return enhanced

    def _ctx(self, jd, role, level):
        parts = []
        if role:  parts.append(f"Target Role: {role}")
        if level: parts.append(f"Experience Level: {level}")
        if jd:    parts.append(f"Job Description excerpt: {jd[:400]}")
        return "\n".join(parts)

    def _summary_prompt(self, s, ctx):
        return f"""{ctx}

Rewrite this professional summary to be ATS-optimized and impactful.

Original: {s if s else "(none — create one from context)"}

Rules:
- 3-4 sentences, 60-100 words
- No first person ("I", "my", "me") — use third-person style
- Start with role title and years of experience
- Highlight key skills and value proposition
- Remove weak phrases like "I am passionate about"
- Professional, confident tone

Return ONLY the rewritten summary."""

    def _experience_prompt(self, text, ctx):
        return f"""{ctx}

Rewrite these work experience bullet points to be more impactful and ATS-optimized.

Original:
{text[:2000]}

Rules:
- Start each bullet with a strong past-tense action verb
- Remove weak openers: "As an X, I...", "Contributed to", "Helped", "Was responsible for"
- Quantify results where possible (%, scale, numbers)
- Keep company name / date lines exactly as-is
- 1-2 lines per bullet

Return ONLY the improved experience text, same structure."""

    def _bullets_prompt(self, bullets, ctx):
        return f"""{ctx}

Rewrite these bullets to start with strong action verbs and show measurable impact:

{bullets}

Return ONLY the improved bullets, one per line."""

    def _projects_prompt(self, text, ctx):
        return f"""{ctx}

Improve this projects section for ATS optimization:

{text[:1500]}

Rules: highlight technologies, show impact, active voice, quantify if possible.
Return ONLY the improved text."""

    def _skills_prompt(self, skills, jd, role):
        return f"""Target Role: {role}
Current skills: {', '.join(skills)}
JD keywords: {jd[:300] if jd else 'not provided'}

Add relevant missing skills for this role to the list.
Return ONLY a comma-separated list, max 25 skills total, no explanations."""

    def _call(self, prompt: str, max_tokens: int = 500) -> str:
        """Single GPT call. Sets _quota_exceeded=True on 429 and raises to abort chain."""
        if self._quota_exceeded:
            return ""
        try:
            resp = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "Expert resume writer and ATS specialist. "
                                "Return only the requested content — no preamble, no commentary."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if '429' in err or 'quota' in err.lower() or 'insufficient_quota' in err:
                self._quota_exceeded = True
                print("[AIEnhancer] OpenAI quota exceeded — switching to rule-based enhancement.")
                raise   # bubble up so _gpt_enhance stops immediately
            print(f"[AIEnhancer] GPT call error: {err}")
            return ""

    def _is_improved(self, enhanced: dict, original: dict) -> bool:
        for key in ('summary', 'experience_text', 'projects_text'):
            orig = (original.get(key) or "").strip()
            new  = (enhanced.get(key) or "").strip()
            if orig and new and orig != new:
                return True
        return False

 

    def _rule_enhance(self, data: Dict, target_role: str = "", jd: str = "") -> Dict:
        enhanced = dict(data)

        
        enhanced['summary'] = self._rewrite_summary(
            data.get('summary', ''),
            data.get('skills', []),
            data.get('experience_text', ''),
            target_role,
        )

       
        if data.get('experience_text'):
            enhanced['experience_text'] = self._rewrite_bullets(data['experience_text'])

       
        if data.get('experience_entries'):
            new_entries = []
            for exp in data['experience_entries']:
                e = dict(exp)
                if exp.get('responsibilities'):
                    resp_text = '\n'.join(exp['responsibilities']) if isinstance(exp['responsibilities'], list) else exp['responsibilities']
                    rewritten = self._rewrite_bullets(resp_text)
                    e['responsibilities'] = rewritten.split('\n')
                new_entries.append(e)
            enhanced['experience_entries'] = new_entries
           
            parts = []
            for exp in new_entries:
                header = f"{exp.get('title','')} | {exp.get('company','')} ({exp.get('duration','')})"
                resps  = exp.get('responsibilities', [])
                if isinstance(resps, list):
                    lines = ['• ' + r.lstrip('• ') for r in resps if r.strip()]
                else:
                    lines = [resps]
                parts.append(header + '\n' + '\n'.join(lines))
            if parts:
                enhanced['experience_text'] = '\n\n'.join(parts)

        
        if data.get('projects_text'):
            enhanced['projects_text'] = self._rewrite_bullets(data['projects_text'])

       
        enhanced['skills'] = self._expand_skills(data.get('skills', []), target_role, jd)

        enhanced['full_text'] = self._build_full_text(enhanced)
        return enhanced

    def _rewrite_summary(self, original: str, skills: list, exp_text: str, role: str) -> str:
        skills_str = ', '.join(skills[:5]) if skills else 'modern technologies'
        role_str   = role or self._infer_role(exp_text, skills)

        yr_match = re.search(r'(\d+)\+?\s*year', original, re.I)
        yrs_str  = f"{yr_match.group(1)}+ years of " if yr_match else ""

        impact = self._extract_impact(exp_text)
        impact_sentence = f" {impact}" if impact else ""

        return (
            f"Results-driven {role_str} with {yrs_str}hands-on expertise in {skills_str}. "
            f"Proven ability to design and deliver scalable, high-quality solutions that drive measurable impact.{impact_sentence} "
            f"Thrives in collaborative environments with a strong focus on engineering excellence, continuous learning, and innovation."
        )

    def _rewrite_bullets(self, text: str) -> str:
        replacements = [
            (r'^As an? [\w\s]+ at [\w\s]+, I\s+', ''),
            (r'^As an? [\w\s]+, I\s+',             ''),
            (r'^I contributed to\b',               'Collaborated to deliver'),
            (r'^Contributed to the design and development of\b', 'Designed and developed'),
            (r'^Contributed to\b',                 'Collaborated to deliver'),
            (r'^Leading the development of\b',     'Led end-to-end development of'),
            (r'^Was responsible for\b',            'Managed'),
            (r'^Helped (with |to )?',              'Assisted in '),
            (r'^Worked on\b',                      'Developed'),
            (r'^Used\b',                           'Leveraged'),
            (r'^Made\b',                           'Created'),
            (r'^Did\b',                            'Executed'),
            (r'^Provided\b',                       'Delivered'),
            (r'^Implemented a\b',                  'Engineered a'),
            (r'^Designed to\b',                    'Developed to'),
        ]

        lines     = text.split('\n')
        rewritten = []
        for line in lines:
            stripped = line.strip().lstrip('•-* ')
            if not stripped:
                rewritten.append(line)
                continue

            improved = stripped
            for pattern, replacement in replacements:
                new = re.sub(pattern, replacement, improved, count=1, flags=re.IGNORECASE)
                if new != improved:
                    improved = new.strip()
                    break

            # Capitalise first letter
            if improved and improved[0].islower():
                improved = improved[0].upper() + improved[1:]

            prefix = '• ' if line.startswith('• ') else ('- ' if line.startswith('- ') else '')
            rewritten.append(prefix + improved)

        return '\n'.join(rewritten)

    def _expand_skills(self, skills: list, role: str, jd: str) -> list:
        existing_lower = {s.lower() for s in skills}
        role_map = {
            'flutter': ['Flutter', 'Dart', 'Android', 'iOS', 'Firebase', 'REST API', 'Mobile Development'],
            'android': ['Android', 'Kotlin', 'Java', 'Firebase', 'REST API', 'Material Design'],
            'frontend':['HTML', 'CSS', 'JavaScript', 'React', 'Responsive Design', 'UI/UX'],
            'backend': ['Node.js', 'REST API', 'SQL', 'MongoDB', 'Express', 'Microservices'],
            'python':  ['Python', 'Django', 'FastAPI', 'Pandas', 'NumPy', 'SQL'],
            'ml':      ['Machine Learning', 'Python', 'TensorFlow', 'Scikit-learn', 'Data Analysis'],
            'aiml':    ['Python', 'TensorFlow', 'PyTorch', 'NLP', 'Machine Learning', 'Deep Learning'],
        }
        all_text = (role + ' ' + ' '.join(skills)).lower()
        to_add   = []
        for key, extras in role_map.items():
            if key in all_text:
                for s in extras:
                    if s.lower() not in existing_lower:
                        to_add.append(s)

        professional = ['Git', 'Agile', 'Problem Solving', 'Team Collaboration', 'Communication']
        for s in professional:
            if s.lower() not in existing_lower:
                to_add.append(s)

        return list(dict.fromkeys(skills + to_add))[:25]

    def _infer_role(self, exp_text, skills):
        text = (exp_text + ' ' + ' '.join(skills)).lower()
        if 'flutter' in text: return 'Flutter Developer'
        if 'machine learning' in text or 'aiml' in text: return 'AI/ML Engineer'
        if 'react' in text or 'frontend' in text: return 'Frontend Developer'
        if 'node' in text or 'backend' in text: return 'Backend Developer'
        if 'python' in text: return 'Python Developer'
        return 'Software Developer'

    def _extract_impact(self, exp_text: str) -> str:
        for line in exp_text.split('\n'):
            if re.search(r'\d+', line) and 20 < len(line) < 120:
                return line.strip().lstrip('•-* ')
        return ""

    def _build_full_text(self, data: Dict) -> str:
        parts = []
        for k in ['name','email','summary','experience_text','education_text','projects_text']:
            if data.get(k): parts.append(str(data[k]))
        if data.get('skills'):         parts.append(', '.join(data['skills']))
        if data.get('certifications'): parts.append(', '.join(data['certifications']))
        for e in data.get('experience_entries', []):
            for f in ['title','company']:
                if e.get(f): parts.append(str(e[f]))
            resps = e.get('responsibilities', [])
            if isinstance(resps, list): parts.extend(resps)
            elif resps: parts.append(str(resps))
        for e in data.get('project_entries', []):
            for f in ['name','tech','description']:
                if e.get(f): parts.append(str(e[f]))
        return ' '.join(parts)