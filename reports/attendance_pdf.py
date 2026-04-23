import io
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)

class AttendanceReportBuilder:
    def __init__(self, data):
        """
        data: List of dicts with {name, usn, subject, total, present, percentage}
        """
        self.data = data

    def generate_chart(self):
        """Creates a bar chart of attendance percentages for students."""
        if not self.data:
            return None

        # Take top 10 or unique students for the chart to avoid clutter
        unique_students = {}
        for item in self.data:
            if item['usn'] not in unique_students:
                unique_students[item['usn']] = {
                    'name': item['name'],
                    'percentages': []
                }
            unique_students[item['usn']]['percentages'].append(item['percentage'])
        
        # Calculate average per student
        chart_data = []
        for usn, info in list(unique_students.items())[:15]: # Limit to 15 students
            avg = sum(info['percentages']) / len(info['percentages'])
            chart_data.append((usn, avg))

        usns = [d[0] for d in chart_data]
        avgs = [d[1] for d in chart_data]

        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(8, 4))
        
        colors_list = ['#16a34a' if x >= 75 else '#dc2626' for x in avgs]
        bars = ax.bar(usns, avgs, color=colors_list, width=0.6)
        
        ax.axhline(y=75, color='#2563eb', linestyle='--', alpha=0.5, label='Threshold (75%)')
        ax.set_ylabel("Attendance %", fontsize=10, fontweight='bold')
        ax.set_title("Attendance Distribution by Student (Average %)", fontsize=12, fontweight='bold', pad=15)
        ax.set_ylim(0, 105)
        
        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    def build_pdf(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=40, bottomMargin=40
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading1'],
            alignment=1,
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=5
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            alignment=1,
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#64748b"),
            spaceAfter=20
        )
        
        # --- Header ---
        elements.append(Paragraph("Engineering College Management System", header_style))
        elements.append(Paragraph("Consolidated Attendance Report", subtitle_style))
        
        # --- Table ---
        table_header = [
            Paragraph("<b>Student Name</b>", styles['Normal']), 
            Paragraph("<b>USN</b>", styles['Normal']), 
            Paragraph("<b>Subject</b>", styles['Normal']), 
            Paragraph("<b>Total</b>", styles['Normal']),
            Paragraph("<b>Present</b>", styles['Normal']),
            Paragraph("<b>%</b>", styles['Normal'])
        ]
        table_data = [table_header]
        
        for item in self.data:
            perc_color = "#16a34a" if item['percentage'] >= 75 else "#dc2626"
            table_data.append([
                Paragraph(item['name'], styles['Normal']),
                item['usn'],
                Paragraph(f"<font size=8>{item['subject']}</font>", styles['Normal']),
                str(item['total']),
                str(item['present']),
                Paragraph(f"<b><font color='{perc_color}'>{item['percentage']}%</font></b>", styles['Normal'])
            ])

        attendance_table = Table(table_data, colWidths=[1.8*inch, 1*inch, 2.5*inch, 0.6*inch, 0.7*inch, 0.7*inch], repeatRows=1)
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(attendance_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # --- Chart ---
        chart_buf = self.generate_chart()
        if chart_buf:
            img = Image(chart_buf, width=7*inch, height=3.5*inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.4*inch))

        # --- Footer ---
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        footer_style = ParagraphStyle('FooterStyle', fontSize=8, textColor=colors.grey)
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Report Generated on: {now}", footer_style))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("__________________________", footer_style))
        elements.append(Paragraph("<b>Authorized Signature</b>", footer_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer
