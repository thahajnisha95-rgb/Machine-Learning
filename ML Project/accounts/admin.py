from django.contrib import admin
from .models import StudentProfile, Skill, LearningResource, StudentResourceProgress


class LearningResourceInline(admin.TabularInline):
    model = LearningResource
    extra = 1


class StudentResourceProgressInline(admin.TabularInline):
    model = StudentResourceProgress
    extra = 0


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'course', 'year_of_study')
    search_fields = ('full_name', 'course', 'user__username', 'interests')
    list_filter = ('year_of_study', 'course')
    inlines = [StudentResourceProgressInline]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'resource_count', 'created_at')
    search_fields = ('name', 'category', 'keywords', 'description')
    list_filter = ('category',)
    inlines = [LearningResourceInline]

    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = "Resources"


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'skill', 'platform', 'resource_type', 'difficulty', 'is_active')
    search_fields = ('title', 'description', 'platform', 'skill__name')
    list_filter = ('resource_type', 'difficulty', 'is_active', 'skill')


@admin.register(StudentResourceProgress)
class StudentResourceProgressAdmin(admin.ModelAdmin):
    list_display = ('profile', 'resource', 'status', 'rating', 'updated_at')
    list_filter = ('status', 'rating', 'resource__skill')
    search_fields = ('profile__full_name', 'resource__title', 'notes')