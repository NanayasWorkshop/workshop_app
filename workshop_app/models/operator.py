from django.db import models
from django.contrib.auth.models import User
from .machine import Machine


class Operator(models.Model):
    """Human operators/workers"""
    operator_id = models.CharField(max_length=15, unique=True)  # HUM-001
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to Django user
    specialization = models.CharField(max_length=100, blank=True)
    
    SKILL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert')
    ]
    skill_level = models.CharField(max_length=20, choices=SKILL_CHOICES, default='intermediate')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Machine certifications as a many-to-many relationship
    certified_machines = models.ManyToManyField(Machine, blank=True, related_name='certified_operators')
    
    special_skills = models.TextField(blank=True)
    productivity_factor = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    
    def __str__(self):
        return f"{self.operator_id} - {self.user.get_full_name() or self.user.username}"
    
    def get_active_jobs(self):
        """Get all active jobs assigned to this operator"""
        # This is a placeholder method - we'll implement this once we have the Job model
        return []
