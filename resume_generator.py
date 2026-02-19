import io
from typing import Dict, Optional


class ResumeGenerator:
    """
    Generate professional resumes in DOCX and PDF formats
    Supports multiple templates
    """
    
    
    TEMPLATES = {
        "Classic Professional": {
            "header_color": "2C3E50",
            "accent_color": "2980B9",
            "secondary_color": "ECF0F1",
            "font_name": "Arial",
            "header_style": "traditional"
        },
        "Modern Minimalist": {
            "header_color": "1A1A2E",
            "accent_color": "16213E",
            "secondary_color": "E8F4FD",
            "font_name": "Calibri",
            "header_style": "modern"
        },
        "Executive Bold": {
            "header_color": "1B2631",
            "accent_color": "C0392B",
            "secondary_color": "FDFEFE",
            "font_name": "Georgia",
            "header_style": "executive"
        }
    }
    
    def generate_docx(self, resume_data: Dict, template_name: str = "Classic Professional") -> bytes:
        """Generate a professional DOCX resume"""
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
        from docx.enum.style import WD_STYLE_TYPE
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        import re
        
        template = self.TEMPLATES.get(template_name, self.TEMPLATES["Classic Professional"])
        
        doc = Document()
        
       
        for section in doc.sections:
            section.top_margin = Inches(0.7)
            section.bottom_margin = Inches(0.7)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
        
        def hex_to_rgb(hex_color: str):
            h = hex_color.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        
        accent_rgb = hex_to_rgb(template['accent_color'])
        header_rgb = hex_to_rgb(template['header_color'])
        
        def add_horizontal_line(doc, color_hex="2980B9", thickness=15):
            """Add a colored horizontal line"""
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), str(thickness))
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), color_hex)
            pBdr.append(bottom)
            pPr.append(pBdr)
            return p
        
        def add_section_header(doc, title: str, template: dict):
            """Add a styled section header"""
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(11)
            run.font.name = template['font_name']
            run.font.color.rgb = RGBColor(*hex_to_rgb(template['accent_color']))
            add_horizontal_line(doc, template['accent_color'], 12)
            return p
        
        def add_paragraph(doc, text: str, font_size: int = 10, bold: bool = False, 
                          italic: bool = False, indent: bool = False, space_after: int = 2):
            """Add a styled paragraph"""
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(space_after)
            if indent:
                p.paragraph_format.left_indent = Inches(0.15)
            
            run = p.add_run(text)
            run.font.size = Pt(font_size)
            run.font.name = template['font_name']
            run.bold = bold
            run.italic = italic
            return p
        
        name = resume_data.get('name', 'Your Name')
        
        
        name_para = doc.add_paragraph()
        name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_para.paragraph_format.space_before = Pt(0)
        name_para.paragraph_format.space_after = Pt(7)
        name_run = name_para.add_run(name)
        name_run.bold = True
        name_run.font.size = Pt(24)
        name_run.font.name = template['font_name']
        name_run.font.color.rgb = RGBColor(*header_rgb)
        
       
        contact_parts = []
        if resume_data.get('email'):
            contact_parts.append(resume_data['email'])
        if resume_data.get('phone'):    
            contact_parts.append(resume_data['phone'])
        if resume_data.get('location'):
            contact_parts.append(resume_data['location'])
        if resume_data.get('linkedin'):
            contact_parts.append(resume_data['linkedin'])
        if resume_data.get('website'):
            contact_parts.append(resume_data['website'])
        
        if contact_parts:
            contact_para = doc.add_paragraph()
            contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            contact_para.paragraph_format.space_before = Pt(4)
            contact_para.paragraph_format.space_after = Pt(8)
            contact_run = contact_para.add_run(" | ".join(contact_parts))
            contact_run.font.size = Pt(10.5)
            contact_run.font.name = template['font_name']
            contact_run.font.color.rgb = RGBColor(80, 80, 80)
        
       
        add_horizontal_line(doc, template['accent_color'], 20)
        
        
        summary = resume_data.get('summary', '')
        if summary:
            add_section_header(doc, "Professional Summary", template)
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(summary)
            run.font.size = Pt(10)
            run.font.name = template['font_name']
        
       
        def add_experience_section():
            
            exp_entries = resume_data.get('experience_entries', [])
            exp_text = resume_data.get('experience_text', '')
            
            if exp_entries and any(e.get('title') for e in exp_entries):
                add_section_header(doc, "Work Experience", template)
                
                for exp in exp_entries:
                    if not exp.get('title'):
                        continue
                    
                  
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(4)
                    p.paragraph_format.space_after = Pt(1)
                    
                    title_run = p.add_run(exp.get('title', ''))
                    title_run.bold = True
                    title_run.font.size = Pt(10.5)
                    title_run.font.name = template['font_name']
                    title_run.font.color.rgb = RGBColor(*header_rgb)
                    
                    if exp.get('company'):
                        company_run = p.add_run(f"  |  {exp['company']}")
                        company_run.font.size = Pt(10)
                        company_run.font.name = template['font_name']
                        company_run.font.color.rgb = RGBColor(100, 100, 100)
                    
                    
                    if exp.get('duration') or exp.get('location'):
                        meta_parts = []
                        if exp.get('duration'):
                            meta_parts.append(exp['duration'])
                        if exp.get('location'):
                            meta_parts.append(exp['location'])
                        
                        p2 = doc.add_paragraph()
                        p2.paragraph_format.space_before = Pt(0)
                        p2.paragraph_format.space_after = Pt(2)
                        meta_run = p2.add_run(" | ".join(meta_parts))
                        meta_run.italic = True
                        meta_run.font.size = Pt(9.5)
                        meta_run.font.name = template['font_name']
                        meta_run.font.color.rgb = RGBColor(120, 120, 120)
                    
                 
                    if exp.get('responsibilities'):
                        for bullet in exp['responsibilities'].split('\n'):
                            bullet = bullet.strip().lstrip('•-* ')
                            if bullet:
                                p_bullet = doc.add_paragraph(style='List Bullet')
                                p_bullet.paragraph_format.space_before = Pt(1)
                                p_bullet.paragraph_format.space_after = Pt(1)
                                p_bullet.paragraph_format.left_indent = Inches(0.3)
                                bullet_run = p_bullet.add_run(bullet)
                                bullet_run.font.size = Pt(10)
                                bullet_run.font.name = template['font_name']
            
            elif exp_text:
                add_section_header(doc, "Work Experience", template)
            
                lines = exp_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                   
                    if re.match(r'^.{5,50}(at|@|\|).{3,50}', line, re.IGNORECASE) or \
                       any(word in line.lower() for word in ['engineer', 'manager', 'developer', 'analyst', 'designer', 'lead', 'director']):
                        p = doc.add_paragraph()
                        p.paragraph_format.space_before = Pt(5)
                        p.paragraph_format.space_after = Pt(1)
                        run = p.add_run(line)
                        run.bold = True
                        run.font.size = Pt(10.5)
                        run.font.name = template['font_name']
                        run.font.color.rgb = RGBColor(*header_rgb)
                    elif line.startswith(('•', '-', '*', '·')):
                        p_bullet = doc.add_paragraph(style='List Bullet')
                        p_bullet.paragraph_format.left_indent = Inches(0.3)
                        p_bullet.paragraph_format.space_before = Pt(1)
                        p_bullet.paragraph_format.space_after = Pt(1)
                        bullet_run = p_bullet.add_run(line.lstrip('•-*· '))
                        bullet_run.font.size = Pt(10)
                        bullet_run.font.name = template['font_name']
                    else:
                        p = doc.add_paragraph()
                        p.paragraph_format.space_before = Pt(1)
                        p.paragraph_format.space_after = Pt(1)
                        run = p.add_run(line)
                        run.font.size = Pt(10)
                        run.font.name = template['font_name']
        
        add_experience_section()
        
       
        edu_entries = resume_data.get('education_entries', [])
        edu_text = resume_data.get('education_text', '')
        
        if edu_entries and any(e.get('degree') for e in edu_entries) or edu_text:
            add_section_header(doc, "Education", template)
            
            if edu_entries and any(e.get('degree') for e in edu_entries):
                for edu in edu_entries:
                    if not edu.get('degree'):
                        continue
                    
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(1)
                    
                    deg_run = p.add_run(edu.get('degree', ''))
                    deg_run.bold = True
                    deg_run.font.size = Pt(10.5)
                    deg_run.font.name = template['font_name']
                    deg_run.font.color.rgb = RGBColor(*header_rgb)
                    
                    inst_parts = []
                    if edu.get('institution'):
                        inst_parts.append(edu['institution'])
                    if edu.get('year'):
                        inst_parts.append(edu['year'])
                    if edu.get('gpa'):
                        inst_parts.append(f"GPA: {edu['gpa']}")
                    
                    if inst_parts:
                        p2 = doc.add_paragraph()
                        p2.paragraph_format.space_before = Pt(0)
                        p2.paragraph_format.space_after = Pt(3)
                        meta_run = p2.add_run(" | ".join(inst_parts))
                        meta_run.italic = True
                        meta_run.font.size = Pt(9.5)
                        meta_run.font.name = template['font_name']
                        meta_run.font.color.rgb = RGBColor(100, 100, 100)
            elif edu_text:
                for line in edu_text.split('\n'):
                    if line.strip():
                        add_paragraph(doc, line.strip(), space_after=2)
        
       
        skills = resume_data.get('skills', [])
        if skills:
            add_section_header(doc, "Skills & Expertise", template)
            
           
            if len(skills) > 6:
               
                chunk_size = max(3, len(skills) // 3)
                chunks = [skills[i:i+chunk_size] for i in range(0, len(skills), chunk_size)]
                
                for chunk in chunks[:3]:  # Max 3 rows
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    skills_text = " • ".join(chunk)
                    run = p.add_run(f"▸  {skills_text}")
                    run.font.size = Pt(9.5)
                    run.font.name = template['font_name']
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(4)
                run = p.add_run(" • ".join(skills))
                run.font.size = Pt(10)
                run.font.name = template['font_name']
        
       
        proj_entries = resume_data.get('project_entries', [])
        proj_text = resume_data.get('projects_text', '')
        
        if proj_entries and any(e.get('name') for e in proj_entries) or proj_text:
            add_section_header(doc, "Projects & Achievements", template)
            
            if proj_entries and any(e.get('name') for e in proj_entries):
                for proj in proj_entries:
                    if not proj.get('name'):
                        continue
                    
                    p = doc.add_paragraph()
                    p.paragraph_format.space_before = Pt(4)
                    p.paragraph_format.space_after = Pt(1)
                    
                    name_run = p.add_run(proj.get('name', ''))
                    name_run.bold = True
                    name_run.font.size = Pt(20)
                    name_run.font.name = template['font_name']
                    name_run.font.color.rgb = RGBColor(*hex_to_rgb(template['accent_color']))
                    
                    if proj.get('tech'):
                        tech_run = p.add_run(f"  |  {proj['tech']}")
                        tech_run.italic = True
                        tech_run.font.size = Pt(9.5)
                        tech_run.font.name = template['font_name']
                        tech_run.font.color.rgb = RGBColor(100, 100, 100)
                    
                    if proj.get('description'):
                        for line in proj['description'].split('\n'):
                            line = line.strip().lstrip('•-* ')
                            if line:
                                p2 = doc.add_paragraph(style='List Bullet')
                                p2.paragraph_format.left_indent = Inches(0.3)
                                p2.paragraph_format.space_before = Pt(1)
                                p2.paragraph_format.space_after = Pt(1)
                                desc_run = p2.add_run(line)
                                desc_run.font.size = Pt(10)
                                desc_run.font.name = template['font_name']
            
            elif proj_text:
                for line in proj_text.split('\n'):
                    if line.strip():
                        if line.strip()[0].isupper() and len(line.strip()) < 60:
                            p = doc.add_paragraph()
                            p.paragraph_format.space_before = Pt(4)
                            p.paragraph_format.space_after = Pt(1)
                            run = p.add_run(line.strip())
                            run.bold = True
                            run.font.size = Pt(10.5)
                            run.font.name = template['font_name']
                        else:
                            add_paragraph(doc, line.strip(), indent=True, space_after=1)
        
       
        certs = resume_data.get('certifications', [])
        if certs:
            add_section_header(doc, "Certifications", template)
            for cert in certs:
                if cert.strip():
                    p = doc.add_paragraph(style='List Bullet')
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    run = p.add_run(cert.strip())
                    run.font.size = Pt(10)
                    run.font.name = template['font_name']
        
       
        languages = resume_data.get('languages', '')
        if languages:
            add_section_header(doc, "Languages", template)
            add_paragraph(doc, languages, space_after=4)
        
        
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer.read()
    
    def generate_pdf(self, resume_data: Dict, template_name: str = "Classic Professional") -> bytes:
        """Generate PDF resume using ReportLab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            template = self.TEMPLATES.get(template_name, self.TEMPLATES["Classic Professional"])
            
            def hex_to_color(hex_str):
                h = hex_str.lstrip('#')
                r, g, b = int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255
                return colors.Color(r, g, b)
            
            accent_color = hex_to_color(template['accent_color'])
            header_color = hex_to_color(template['header_color'])
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.7*inch,
                bottomMargin=0.7*inch
            )
            
            styles = getSampleStyleSheet()
            
            
            name_style = ParagraphStyle('NameStyle',
                fontName='Helvetica-Bold',
                fontSize=22,
                textColor=header_color,
                alignment=TA_CENTER,
                spaceAfter=4
            )
            
            contact_style = ParagraphStyle('ContactStyle',
                fontName='Helvetica',
                fontSize=9,
                textColor=colors.Color(0.4, 0.4, 0.4),
                alignment=TA_CENTER,
                spaceAfter=6
            )
            
            section_header_style = ParagraphStyle('SectionHeader',
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=accent_color,
                spaceBefore=10,
                spaceAfter=2
            )
            
            body_style = ParagraphStyle('BodyStyle',
                fontName='Helvetica',
                fontSize=10,
                textColor=colors.black,
                spaceAfter=3,
                leading=14
            )
            
            job_title_style = ParagraphStyle('JobTitle',
                fontName='Helvetica-Bold',
                fontSize=10.5,
                textColor=header_color,
                spaceBefore=6,
                spaceAfter=1
            )
            
            meta_style = ParagraphStyle('MetaStyle',
                fontName='Helvetica-Oblique',
                fontSize=9.5,
                textColor=colors.Color(0.5, 0.5, 0.5),
                spaceAfter=2
            )
            
            story = []
            
            
            story.append(Paragraph(resume_data.get('name', 'Your Name'), name_style))
            
           
            contact_parts = []
            for field in ['email', 'phone', 'location', 'linkedin', 'website']:
                if resume_data.get(field):
                    contact_parts.append(resume_data[field])
            if contact_parts:
                story.append(Paragraph(" | ".join(contact_parts), contact_style))
            
            
            story.append(HRFlowable(width="100%", thickness=2, color=accent_color, spaceAfter=8))
            
          
            if resume_data.get('summary'):
                story.append(Paragraph("PROFESSIONAL SUMMARY", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                story.append(Paragraph(resume_data['summary'], body_style))
            
            
            exp_entries = resume_data.get('experience_entries', [])
            exp_text = resume_data.get('experience_text', '')
            
            if exp_entries and any(e.get('title') for e in exp_entries):
                story.append(Paragraph("WORK EXPERIENCE", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                
                for exp in exp_entries:
                    if not exp.get('title'):
                        continue
                    title_company = exp['title']
                    if exp.get('company'):
                        title_company += f" | {exp['company']}"
                    story.append(Paragraph(title_company, job_title_style))
                    
                    meta_parts = []
                    if exp.get('duration'):
                        meta_parts.append(exp['duration'])
                    if exp.get('location'):
                        meta_parts.append(exp['location'])
                    if meta_parts:
                        story.append(Paragraph(" | ".join(meta_parts), meta_style))
                    
                    if exp.get('responsibilities'):
                        for line in exp['responsibilities'].split('\n'):
                            line = line.strip().lstrip('•-* ')
                            if line:
                                story.append(Paragraph(f"• {line}", body_style))
            
            elif exp_text:
                story.append(Paragraph("WORK EXPERIENCE", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                for line in exp_text.split('\n'):
                    if line.strip():
                        story.append(Paragraph(line.strip(), body_style))
            
           
            edu_entries = resume_data.get('education_entries', [])
            edu_text = resume_data.get('education_text', '')
            
            if edu_entries and any(e.get('degree') for e in edu_entries) or edu_text:
                story.append(Paragraph("EDUCATION", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                
                if edu_entries and any(e.get('degree') for e in edu_entries):
                    for edu in edu_entries:
                        if edu.get('degree'):
                            story.append(Paragraph(edu['degree'], job_title_style))
                            meta_parts = []
                            for f in ['institution', 'year', 'gpa']:
                                if edu.get(f):
                                    meta_parts.append(edu[f])
                            if meta_parts:
                                story.append(Paragraph(" | ".join(meta_parts), meta_style))
                elif edu_text:
                    for line in edu_text.split('\n'):
                        if line.strip():
                            story.append(Paragraph(line.strip(), body_style))
           
            skills = resume_data.get('skills', [])
            if skills:
                story.append(Paragraph("SKILLS & EXPERTISE", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                skills_text = " • ".join(skills)
                story.append(Paragraph(skills_text, body_style))
            
            proj_entries = resume_data.get('project_entries', [])
            proj_text = resume_data.get('projects_text', '')
            
            if proj_entries and any(e.get('name') for e in proj_entries) or proj_text:
                story.append(Paragraph("PROJECTS & ACHIEVEMENTS", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                
                if proj_entries and any(e.get('name') for e in proj_entries):
                    for proj in proj_entries:
                        if proj.get('name'):
                            proj_header = proj['name']
                            if proj.get('tech'):
                                proj_header += f" | {proj['tech']}"
                            story.append(Paragraph(proj_header, job_title_style))
                            if proj.get('description'):
                                for line in proj['description'].split('\n'):
                                    line = line.strip().lstrip('•-* ')
                                    if line:
                                        story.append(Paragraph(f"• {line}", body_style))
                elif proj_text:
                    for line in proj_text.split('\n'):
                        if line.strip():
                            story.append(Paragraph(line.strip(), body_style))
            
            certs = resume_data.get('certifications', [])
            if certs:
                story.append(Paragraph("CERTIFICATIONS", section_header_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=accent_color, spaceAfter=4))
                for cert in certs:
                    if cert.strip():
                        story.append(Paragraph(f"• {cert}", body_style))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.read()
        
        except ImportError:
            
            raise Exception("ReportLab not installed. Install with: pip install reportlab")
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
