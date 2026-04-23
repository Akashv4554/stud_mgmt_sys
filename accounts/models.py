"""
accounts/models.py
Custom User model extending AbstractUser with role-based access control.
Roles: admin, faculty, student.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user for the college management system.
    Every person (admin, faculty, or student) authenticates via this model.
    Faculty and Student profiles are linked via OneToOneField back to this model.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        FACULTY = "faculty", "Faculty"
        STUDENT = "student", "Student"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    phone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
