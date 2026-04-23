import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from academics.models import Department, Subject
from students.models import Student, Enrollment
from faculty.models import Faculty, FacultySubjectAssignment
from attendance.models import Attendance
from exams.models import Exam, Marks, Result

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with realistic Engineering College academic data."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Deletes existing data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("--- Starting Realistic Data Seeding ---")

        if options['clear']:
            self.clear_data()

        # 1. Create Core & IT Departments
        departments = self.seed_departments()
        
        # 2. Create Admin
        self.seed_admin()

        # 3. Create Subjects for all semesters (1-8)
        self.seed_subjects(departments)

        # 4. Create Faculty
        faculty_obj_list = self.seed_faculty(departments)

        # 5. Create Exams
        exams_map = self.seed_exams()

        # 6. Create Students and their History
        self.seed_students_and_history(departments, exams_map)

        self.stdout.write(self.style.SUCCESS("\n--- Seeding Completed Successfully ---"))

    def clear_data(self):
        self.stdout.write("Cleaning database...")
        Result.objects.all().delete()
        Marks.objects.all().delete()
        Attendance.objects.all().delete()
        Enrollment.objects.all().delete()
        FacultySubjectAssignment.objects.all().delete()
        Student.objects.all().delete()
        Faculty.objects.all().delete()
        Subject.objects.all().delete()
        Exam.objects.all().delete()
        Department.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

    def seed_departments(self):
        self.stdout.write("Seeding Departments...")
        depts = [
            ("Computer Science & Engineering", "CSE", "it"),
            ("Information Science & Engineering", "ISE", "it"),
            ("Artificial Intelligence & Machine Learning", "AIML", "it"),
            ("Artificial Intelligence & Data Science", "AIDS", "it"),
            ("Electronics & Communication Engineering", "ECE", "core"),
            ("Electrical & Electronics Engineering", "EEE", "core"),
            ("Civil Engineering", "CIVIL", "core"),
            ("Mechanical Engineering", "MECH", "core"),
            ("Cyber Security", "CYBER SECURITY", "it"),
        ]
        dept_objs = {}
        for name, code, group in depts:
            dept, _ = Department.objects.get_or_create(name=name, defaults={"code": code})
            dept_objs[name] = {"obj": dept, "group": group, "code": code}
        return dept_objs

    def seed_admin(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@college.edu", "adminPass123", role=User.Role.ADMIN)
            self.stdout.write("Created Admin: admin / adminPass123")

    def seed_subjects(self, departments):
        self.stdout.write("Seeding Subjects...")

        # Subject name pools keyed by the pool type assigned per department
        theory_pool = {
            "ME": [
                "Thermodynamics", "Fluid Mechanics", "Design of Machines",
                "Heat Transfer", "Manufacturing Processes", "Kinematics",
                "Metrology & Measurements", "Robotics & Automation",
            ],
            "CV": [
                "Structural Analysis", "Surveying", "Concrete Technology",
                "Hydraulics", "Geotechnical Engineering", "Transportation Engg",
                "Environmental Engineering", "Steel Structures",
            ],
            "EE": [
                "Network Analysis", "Control Systems", "Power Electronics",
                "Electrical Machines", "Signals & Systems", "Microcontrollers",
                "Power Systems", "Analog Circuits",
            ],
            "IT": [
                "Data Structures", "Algorithms", "Operating Systems",
                "Database Systems", "Computer Networks", "Software Engineering",
                "Web Programming", "Automata Theory", "Compiler Design",
                "Cloud Computing",
            ],
        }

        # Map each department to a pool key and a short 3-char prefix
        DEPT_META = {
            "Computer Science & Engineering":           {"pool": "IT", "prefix": "CSE"},
            "Information Science & Engineering":        {"pool": "IT", "prefix": "ISE"},
            "Artificial Intelligence & Machine Learning": {"pool": "IT", "prefix": "AIM"},
            "Artificial Intelligence & Data Science":   {"pool": "IT", "prefix": "ADS"},
            "Electronics & Communication Engineering":  {"pool": "EE", "prefix": "ECE"},
            "Electrical & Electronics Engineering":     {"pool": "EE", "prefix": "EEE"},
            "Civil Engineering":                        {"pool": "CV", "prefix": "CIV"},
            "Mechanical Engineering":                   {"pool": "ME", "prefix": "MEC"},
            "Cyber Security":                           {"pool": "IT", "prefix": "CYB"},
        }

        created = skipped = 0

        for dept_name, data in departments.items():
            dept = data["obj"]
            meta = DEPT_META.get(dept_name)
            if not meta:
                # Fallback: derive prefix from first 3 chars of stored dept code
                meta = {"pool": "IT", "prefix": dept.code[:3].upper()}

            prefix = meta["prefix"][:3]          # Always safe: ≤3 chars
            pool   = theory_pool[meta["pool"]]

            for sem in range(1, 9):
                shuffled = pool[:]
                random.shuffle(shuffled)

                # 5 Theory subjects per semester
                for idx in range(1, 6):
                    raw_code = f"{prefix}{sem}{idx:02d}"   # e.g. CSE101 → 7 chars max
                    raw_name = f"{shuffled[idx - 1]} (Sem {sem})"

                    code = raw_code[:30]    # hard safety cap
                    name = raw_name[:150]   # hard safety cap

                    _, c = Subject.objects.get_or_create(
                        code=code,
                        defaults={
                            "name": name,
                            "department": dept,
                            "semester": sem,
                            "credits": 4,
                            "subject_type": Subject.SubjectType.THEORY,
                        },
                    )
                    if c:
                        created += 1
                    else:
                        skipped += 1

                # 1 Lab per semester
                lab_code = f"{prefix}{sem}L1"          # e.g. CSE1L1 → 7 chars max
                lab_name = f"{prefix} Lab - Sem {sem}"

                lab_code = lab_code[:30]
                lab_name = lab_name[:150]

                _, c = Subject.objects.get_or_create(
                    code=lab_code,
                    defaults={
                        "name": lab_name,
                        "department": dept,
                        "semester": sem,
                        "credits": 2,
                        "subject_type": Subject.SubjectType.LAB,
                    },
                )
                if c:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            f"  Subjects: {created} created, {skipped} already existed."
        )

    def seed_faculty(self, departments):
        self.stdout.write("Seeding Faculty...")
        first_names = ["Akash", "Rahul", "Priya", "Sneha", "Rohan", "Kavya", "Arjun", "Divya", "Manish", "Anjali"]
        last_names = ["Patil", "Sharma", "Rao", "Kumar", "Desai", "Joshi", "Singh", "Kulkarni"]
        
        faculty_obj_list = []
        count = 1
        for code, data in departments.items():
            num_faculty = random.randint(8, 12) if data["group"] == "it" else 5
            for _ in range(num_faculty):
                username = f"faculty{count}"
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                user = User.objects.create_user(
                    username=username, password="faculty123", role=User.Role.FACULTY,
                    first_name=fname, last_name=lname
                )
                # Use update_or_create because post_save signals might have already created a profile
                fac, _ = Faculty.objects.update_or_create(
                    user=user,
                    defaults={
                        "department": data["obj"],
                        "employee_id": f"EMP{str(count).zfill(3)}",
                        "designation": "Assistant Professor"
                    }
                )
                faculty_obj_list.append(fac)
                count += 1
                
                # Assign one random subject from their department
                dept_subjects = Subject.objects.filter(department=data["obj"])
                if dept_subjects:
                    FacultySubjectAssignment.objects.create(
                        faculty=fac, subject=random.choice(dept_subjects),
                        academic_year="2025-26", section="A"
                    )
        self.stdout.write(f"Total Faculty: {count-1}")
        return faculty_obj_list

    def seed_exams(self):
        self.stdout.write("Seeding Exams...")
        exams_map = {}
        for sem in range(1, 9):
            # Internals (CIA 1, 2, 3) — out of 50
            for i in range(1, 4):
                exam, _ = Exam.objects.get_or_create(
                    name=f"CIA {i} - Sem {sem}",
                    defaults={
                        "semester": sem,
                        "exam_type": Exam.ExamType.INTERNAL,
                        "academic_year": "2025-26",
                        "max_marks": 50,
                    },
                )
                exams_map.setdefault(sem, []).append(exam)
            # Final Semester Exam — out of 100
            final, _ = Exam.objects.get_or_create(
                name=f"Semester Final - Sem {sem}",
                defaults={
                    "semester": sem,
                    "exam_type": Exam.ExamType.EXTERNAL,
                    "academic_year": "2025-26",
                    "max_marks": 100,
                },
            )
            exams_map.setdefault(sem, []).append(final)
        return exams_map

    def seed_students_and_history(self, departments, exams_map):
        self.stdout.write("Seeding Students with exact distribution...")
        
        department_student_map = {
            "Computer Science & Engineering": 180,
            "Information Science & Engineering": 80,
            "Artificial Intelligence & Machine Learning": 50,
            "Artificial Intelligence & Data Science": 50,
            "Electronics & Communication Engineering": 60,
            "Electrical & Electronics Engineering": 45,
            "Civil Engineering": 36,
            "Mechanical Engineering": 20,
            "Cyber Security": 38
        }

        dept_code_map = {
            "Computer Science & Engineering": "CS",
            "Information Science & Engineering": "IS",
            "Artificial Intelligence & Machine Learning": "AI",
            "Artificial Intelligence & Data Science": "AD",
            "Electronics & Communication Engineering": "EC",
            "Electrical & Electronics Engineering": "EE",
            "Civil Engineering": "CV",
            "Mechanical Engineering": "ME",
            "Cyber Security": "CSY"
        }

        first_names = ["Arjun", "Aditi", "Bhavya", "Chetan", "Deepak", "Esha", "Farhan", "Gaurav", "Harini", "Ishaan"]
        last_names = ["Kumar", "Sharma", "Reddy", "Patil", "Singh", "Joshi", "Iyer", "Nair", "Verma", "Das"]
        
        student_count = 1
        
        for dept_name, count in department_student_map.items():
            dept_obj = departments[dept_name]["obj"]
            dept_code = dept_code_map[dept_name]
            
            self.stdout.write(f"Seeding {count} students for {dept_name}...")
            
            for i in range(1, count + 1):
                # USN logic: 1RV<YEAR><DEPT><ROLL>
                year = random.choice([21, 22, 23])
                usn = f"1RV{year}{dept_code}{str(i).zfill(3)}"
                
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                
                user = User.objects.create_user(
                    username=usn, 
                    password="student123", 
                    role=User.Role.STUDENT,
                    first_name=f"{fname}{i}", 
                    last_name=lname
                )
                
                semester = random.randint(1, 8)
                
                student, _ = Student.objects.update_or_create(
                    user=user,
                    defaults={
                        "usn": usn,
                        "department": dept_obj,
                        "semester": semester,
                        "section": random.choice(["A", "B"])
                    }
                )
                
                # --- Historical Generation ---
                for s in range(1, semester + 1):
                    is_completed = s < semester
                    self.generate_semester_data(student, dept_obj, s, exams_map.get(s, []), is_completed)
                
                # Final update of global percentage
                student.update_attendance_percentage()
                
                student_count += 1

        self.stdout.write("\nFinal Distribution:")
        for dept_name, count in department_student_map.items():
            code = dept_code_map[dept_name]
            self.stdout.write(f"{code} ({dept_name}) -> {count}")

    def generate_semester_data(self, student, dept, semester, exams, is_completed):
        # 1. Enroll in subjects
        subjects = Subject.objects.filter(department=dept, semester=semester)
        for subj in subjects:
            Enrollment.objects.get_or_create(student=student, subject=subj, academic_year="2025-26")
            
            # 2. Attendance (last 60 days)
            if not Attendance.objects.filter(student=student, subject=subj).exists():
                attendance_list = []
                # For simplicity, we just generate ~40 records for each subject
                for day in range(40):
                    d = date.today() - timedelta(days=day + (8 - semester) * 100) # Shift back for old semesters
                    if d.weekday() < 6:
                        attendance_list.append(Attendance(
                            student=student, subject=subj, date=d, period=random.randint(1, 4),
                            status="present" if random.random() < 0.9 else "absent"
                        ))
                Attendance.objects.bulk_create(attendance_list)

            # 3. Marks
            if not Marks.objects.filter(student=student, subject=subj).exists():
                marks_list = []
                for exam in exams:
                    if not is_completed and exam.exam_type == Exam.ExamType.EXTERNAL:
                        continue # Skip final exam for current semester
                        
                    # Realistic distribution: 60-90% mostly
                    pref_ratio = random.choice([0.65, 0.75, 0.85, 0.45]) # Average, Good, V.Good, Low
                    score = Decimal(str(round(min(max(random.gauss(float(exam.max_marks * Decimal(str(pref_ratio))), float(exam.max_marks * 0.1)), 0), exam.max_marks), 1)))
                    
                    marks_list.append(Marks(
                        student=student, subject=subj, exam=exam, marks_obtained=score
                    ))
                Marks.objects.bulk_create(marks_list)

        # 4. Result/SGPA for completed semesters
        if is_completed:
            self.calculate_and_save_sgpa(student, semester)

    def calculate_and_save_sgpa(self, student, semester):
        marks_qs = Marks.objects.filter(student=student, subject__semester=semester).select_related('subject', 'exam')
        subjects_marks = {}
        for m in marks_qs:
            subjects_marks.setdefault(m.subject.id, {"obtained": 0, "total": 0, "credits": m.subject.credits})
            subjects_marks[m.subject.id]["obtained"] += m.marks_obtained
            subjects_marks[m.subject.id]["total"] += m.exam.max_marks
            
        total_gp_credits = Decimal("0")
        total_credits = 0
        
        for sid, data in subjects_marks.items():
            if data["total"] > 0:
                perc = (data["obtained"] / data["total"]) * 100
                gp = self._get_grade_point(perc)
                total_gp_credits += gp * data["credits"]
                total_credits += data["credits"]
                
        if total_credits > 0:
            sgpa = round(total_gp_credits / Decimal(total_credits), 2)
            Result.objects.update_or_create(
                student=student, semester=semester, academic_year="2025-26",
                defaults={
                    "sgpa": sgpa, 
                    "total_credits": total_credits, 
                    "credits_earned": total_credits,
                    "is_published": True
                }
            )

    def _get_grade_point(self, percentage):
        if percentage >= 90: return Decimal("10")
        if percentage >= 80: return Decimal("9")
        if percentage >= 70: return Decimal("8")
        if percentage >= 60: return Decimal("7")
        if percentage >= 50: return Decimal("6")
        if percentage >= 40: return Decimal("5")
        return Decimal("0")
