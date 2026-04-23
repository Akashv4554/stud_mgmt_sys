from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from students.models import Student
from faculty.models import Faculty
from academics.models import Department
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a Student or Faculty profile 
    when a User is created or updated with the corresponding role.
    """

    # Skip if profile already exists (e.g., created manually before User.save completes)
    if instance.role == User.Role.STUDENT:
        if not hasattr(instance, 'student_profile'):
            dept = Department.objects.first()
            if not dept:
                logger.error(f"Could not create Student profile for {instance.username}: No Departments exist.")
                return
            
            Student.objects.create(
                user=instance,
                usn=f"TEMP_{instance.username}",
                department=dept,
                semester=1
            )
            logger.info(f"Automatically created Student profile (TEMP USN) for {instance.username}")

    elif instance.role == User.Role.FACULTY:
        if not hasattr(instance, 'faculty_profile'):
            dept = Department.objects.first()
            if not dept:
                logger.error(f"Could not create Faculty profile for {instance.username}: No Departments exist.")
                return
            
            Faculty.objects.create(
                user=instance,
                employee_id=f"EMP_{instance.username}",
                department=dept,
                designation="Assistant Professor"
            )
            logger.info(f"Automatically created Faculty profile (EMP ID) for {instance.username}")
