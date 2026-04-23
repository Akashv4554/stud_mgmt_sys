# Engineering College Management System

## Features
- Role-based authentication (Admin, Faculty, Student)
- Student & Faculty management
- Attendance tracking
- Marks & Results system
- PDF Report Generation (ReportLab)

## Tech Stack
- Django
- SQLite
- Bootstrap
- ReportLab
- Matplotlib

## Setup Instructions
```bash
git clone <repo-link>
cd project
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver