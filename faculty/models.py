"""
faculty/models.py
Faculty profile linked to accounts.User and Department.
"""

from django.conf import settings
from django.db import models


class Faculty(models.Model):
    """
    Profile for a user with role='faculty'.
    - Linked 1-to-1 with accounts.User
    - Belongs to one Department (FK)
    - Can be assigned to teach subjects via FacultySubjectAssignment
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faculty_profile",
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        "academics.Department",
        on_delete=models.PROTECT,
        related_name="faculty_members",
    )
    designation = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="e.g. Assistant Professor, Professor",
    )
    date_of_joining = models.DateField(null=True, blank=True)
    specialization = models.CharField(max_length=150, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_id"]
        verbose_name = "Faculty"
        verbose_name_plural = "Faculty Members"

    def __str__(self):
        return f"{self.employee_id} – {self.user.get_full_name() or self.user.username}"


class FacultySubjectAssignment(models.Model):
    """
    Tracks which faculty member teaches which subject in a given academic year.
    """

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="subject_assignments",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="faculty_assignments",
    )
    academic_year = models.CharField(max_length=9, help_text="e.g. 2025-2026")
    section = models.CharField(max_length=1, default="A")

    class Meta:
        unique_together = ("faculty", "subject", "academic_year", "section")
        ordering = ["faculty", "subject"]
        verbose_name = "Faculty Subject Assignment"
        verbose_name_plural = "Faculty Subject Assignments"

    def __str__(self):
        return f"{self.faculty.employee_id} → {self.subject.code} ({self.academic_year})"
