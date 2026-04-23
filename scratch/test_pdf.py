import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from reports.pdf_builder import ReportCardBuilder
from students.models import Student

def test_pdf():
    student = Student.objects.first()
    if not student:
        print("No students found")
        return
    
    print(f"Testing PDF for student: {student.usn}, Semester: {student.semester}")
    builder = ReportCardBuilder(student.id, student.semester)
    if builder.fetch_data():
        print("Data fetched successfully")
        pdf_buf = builder.build_pdf()
        filename = f"test_report_{student.usn}.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_buf.getbuffer())
        print(f"PDF generated: {filename}")
    else:
        print("Failed to fetch data (maybe no marks for this semester?)")

if __name__ == "__main__":
    test_pdf()
