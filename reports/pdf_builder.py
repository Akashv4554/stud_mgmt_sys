import io
from decimal import Decimal
from datetime import datetime

import matplotlib
matplotlib.use('Agg')   # IMPORTANT: disable GUI backend
import matplotlib.pyplot as plt
from django.db.models import Sum
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)

from students.models import Student
from exams.models import Marks, Result
from academics.models import Subject


class ReportCardBuilder:
    def __init__(self, student_id, semester):
        self.student_id = student_id
        self.semester = semester
        self.student = None
        self.subject_data = []
        self.sgpa = Decimal("0.00")
        self.cgpa = Decimal("0.00")

    def fetch_data(self):
        """Fetch student info, marks, and result stats."""
        try:
            self.student = Student.objects.select_related(
                "user", "department"
            ).get(id=self.student_id)
        except Student.DoesNotExist:
            return False

        # Fetch marks for the semester
        marks_qs = Marks.objects.filter(
            student=self.student,
            subject__semester=self.semester
        ).select_related("subject", "exam")

        if not marks_qs.exists():
            return False

        # Aggregate marks by subject
        subjects = {}
        for mark in marks_qs:
            subj_code = mark.subject.code
            if subj_code not in subjects:
                subjects[subj_code] = {
                    "name": mark.subject.name,
                    "internal": Decimal("0"),
                    "external": Decimal("0"),
                }
            
            if mark.exam.exam_type == "internal":
                subjects[subj_code]["internal"] += mark.marks_obtained
            else:
                subjects[subj_code]["external"] += mark.marks_obtained

        self.subject_data = []
        for code, data in subjects.items():
            internal = data["internal"]
            external = data["external"]
            total = internal + external
            self.subject_data.append({
                "code": code,
                "name": data["name"],
                "internal": internal,
                "external": external,
                "total": total
            })

        # Fetch SGPA/CGPA from Result model
        result = Result.objects.filter(
            student=self.student, 
            semester=self.semester
        ).first()
        
        if result:
            self.sgpa = result.sgpa or Decimal("0.00")
            self.cgpa = result.cgpa or Decimal("0.00")
        
        return True

    def generate_chart(self):
        """Create a professional bar chart of marks using Matplotlib."""
        codes = [d["code"] for d in self.subject_data]
        marks = [float(d["total"]) for d in self.subject_data]

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(7, 3.5))
        
        bars = ax.bar(codes, marks, color="#0f172a", width=0.6)
        ax.set_xlabel("Subjects", fontsize=10, fontweight='bold')
        ax.set_ylabel("Total Marks", fontsize=10, fontweight='bold')
        ax.set_title("Academic Performance Analysis", fontsize=12, fontweight='bold', pad=15)
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

        plt.xticks(rotation=0)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    def build_pdf(self):
        """Build the final professional PDF document."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40, leftMargin=40,
            topMargin=40, bottomMargin=40
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            alignment=1, # Center
            fontSize=22,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            alignment=1, # Center
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )
        label_style = ParagraphStyle(
            'LabelStyle',
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#475569")
        )
        value_style = ParagraphStyle(
            'ValueStyle',
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black
        )

        # --- Header Section ---
        # Logo placeholder + College Name
        college_header = [
            [Paragraph("<b>LOGO</b>", styles['Normal']), Paragraph("Engineering College Management System", title_style)]
        ]
        header_table = Table(college_header, colWidths=[1*inch, 6*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'CENTER'),
        ]))
        elements.append(header_table)
        elements.append(Paragraph("Official Academic Report Card", subtitle_style))
        
        # Horizontal Line
        elements.append(Spacer(1, 0.1*inch))
        line_table = Table([[""]], colWidths=[doc.width])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor("#1e293b")),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.25*inch))

        # --- Student Details Section ---
        student_info = [
            [Paragraph("Student Name:", label_style), Paragraph(self.student.user.get_full_name() or self.student.user.username, value_style),
             Paragraph("USN:", label_style), Paragraph(self.student.usn, value_style)],
            [Paragraph("Department:", label_style), Paragraph(self.student.department.name, value_style),
             Paragraph("Semester:", label_style), Paragraph(str(self.semester), value_style)],
        ]
        info_table = Table(student_info, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))

        # --- Marks Table ---
        marks_header = [
            Paragraph("<b>Subject Code / Name</b>", styles['Normal']), 
            Paragraph("<b>Internal</b>", styles['Normal']), 
            Paragraph("<b>External</b>", styles['Normal']), 
            Paragraph("<b>Total</b>", styles['Normal'])
        ]
        marks_data = [marks_header]
        
        for item in self.subject_data:
            marks_data.append([
                Paragraph(f"<b>{item['code']}</b><br/><font size=9 color='#64748b'>{item['name']}</font>", styles['Normal']),
                str(item['internal']),
                str(item['external']),
                str(item['total'])
            ])

        marks_table = Table(marks_data, colWidths=[3.5*inch, 1*inch, 1*inch, 1*inch], repeatRows=1)
        marks_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(marks_table)
        elements.append(Spacer(1, 0.3*inch))

        # --- SGPA / CGPA Section ---
        gpa_data = [
            [Paragraph(f"<b>SGPA:</b> {self.sgpa}", styles['Normal']), Paragraph(f"<b>CGPA:</b> {self.cgpa}", styles['Normal'])]
        ]
        gpa_table = Table(gpa_data, colWidths=[3.5*inch, 3*inch])
        gpa_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ]))
        elements.append(gpa_table)
        elements.append(Spacer(1, 0.4*inch))

        # --- Performance Chart ---
        chart_buf = self.generate_chart()
        img = Image(chart_buf, width=6*inch, height=3*inch)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 0.6*inch))

        # --- Footer Section ---
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        footer_content = [
            [Paragraph(f"Generated on: {now}", value_style), "", Paragraph("__________________________", value_style)],
            ["", "", Paragraph("<b>Controller of Examinations</b>", value_style)]
        ]
        footer_table = Table(footer_content, colWidths=[3*inch, 1.5*inch, 2.5*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (2,0), (2,1), 'CENTER'),
        ]))
        elements.append(footer_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

