from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    full_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    year_of_study = models.PositiveIntegerField()
    interests = models.TextField(blank=True)

    def get_interests_list(self):
        if not self.interests:
            return []
        import re
        tokens = re.split(r'[,;\n]+', self.interests)
        return [t.strip() for t in tokens if t.strip()]

    def __str__(self):
        return self.full_name or f"Profile for {self.user.username}"


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. Programming, AI/ML, Data Science, Web Development")
    description = models.TextField(blank=True)
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords or aliases for matching")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_keywords_list(self):
        items = [self.name.lower()]
        if self.category:
            items.append(self.category.lower())
        if self.keywords:
            items.extend([k.strip().lower() for k in self.keywords.split(",") if k.strip()])
        return list(dict.fromkeys(items))


class LearningResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('course', 'Online Course'),
        ('tutorial', 'Tutorial / Guide'),
        ('video', 'Video Lecture'),
        ('documentation', 'Official Documentation'),
        ('book', 'Book / Reference'),
        ('project', 'Hands-on Project'),
    ]

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=30, choices=RESOURCE_TYPE_CHOICES, default='course')
    url = models.URLField(max_length=500)
    platform = models.CharField(max_length=100, blank=True, help_text="e.g. Coursera, YouTube, Docs, edX, GitHub")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['skill', 'difficulty', 'title']

    def __str__(self):
        return f"{self.title} ({self.skill.name})"


class StudentResourceProgress(models.Model):
    STATUS_CHOICES = [
        ('saved', 'Saved for Later'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='saved'
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Student rating from 1 (lowest) to 5 (highest)"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'resource')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.profile.full_name} - {self.resource.title} [{self.status}]"
