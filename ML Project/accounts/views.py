from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import StudentProfile, Skill, LearningResource, StudentResourceProgress
from .forms import StudentProfileForm
from .registration_forms import StudentRegistrationForm
from student_learning_system import get_recommendations_for_student


def register(request):
    """Register a new student account and automatically provision a student profile."""
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "full_name": user.username,
                    "course": "",
                    "year_of_study": 1,
                    "interests": "",
                }
            )
            messages.success(
                request,
                "Account created successfully! You can now log in."
            )
            return redirect("login")
    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


@login_required
def dashboard(request):
    """Main student dashboard displaying profile, ML recommendations, and progress tracking."""
    profile = StudentProfile.objects.filter(user=request.user).first()

    recommendation_data = None
    if profile:
        recommendation_data = get_recommendations_for_student(profile, top_n=6)

    # Student progress records and metrics
    progress_qs = StudentResourceProgress.objects.filter(profile=profile) if profile else []
    completed_count = sum(1 for p in progress_qs if p.status == 'completed')
    in_progress_count = sum(1 for p in progress_qs if p.status == 'in_progress')
    saved_count = sum(1 for p in progress_qs if p.status == 'saved')

    # Mapping of resource_id -> status for template lookups
    resource_status_map = {p.resource_id: p.status for p in progress_qs}

    total_skills = Skill.objects.count()
    learning_resources = LearningResource.objects.filter(
        is_active=True
    ).select_related("skill")
    total_resources = learning_resources.count()

    context = {
        "profile": profile,
        "recommendations": recommendation_data,
        "learning_resources": learning_resources,
        "progress_records": progress_qs,
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "saved_count": saved_count,
        "resource_status_map": resource_status_map,
        "total_skills": total_skills,
        "total_resources": total_resources,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )


@login_required
def edit_profile(request):
    """Edit student profile details (name, degree course, year of study, interests)."""
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.username,
            "course": "",
            "year_of_study": 1,
            "interests": "",
        },
    )

    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Student profile saved successfully!")
            return redirect("dashboard")
    else:
        form = StudentProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile_form.html",
        {
            "form": form,
            "profile": profile,
        }
    )


@login_required
@require_POST
def toggle_resource_progress(request, resource_id):
    """
    Update or delete a student's learning progress record for a resource.
    Supports status: 'saved', 'in_progress', 'completed', 'remove'.
    """
    profile = get_object_or_404(StudentProfile, user=request.user)
    resource = get_object_or_404(LearningResource, id=resource_id)

    status_action = request.POST.get("status", "saved")
    rating_str = request.POST.get("rating")

    if status_action == "remove":
        StudentResourceProgress.objects.filter(profile=profile, resource=resource).delete()
        msg = f"Removed '{resource.title}' from your tracker."
        status_val = None
    else:
        valid_statuses = dict(StudentResourceProgress.STATUS_CHOICES).keys()
        if status_action not in valid_statuses:
            return HttpResponseBadRequest("Invalid status provided.")

        progress_record, created = StudentResourceProgress.objects.get_or_create(
            profile=profile,
            resource=resource,
            defaults={"status": status_action}
        )

        progress_record.status = status_action
        if status_action == "completed" and not progress_record.completed_at:
            progress_record.completed_at = timezone.now()

        if rating_str and rating_str.isdigit():
            rating_val = int(rating_str)
            if 1 <= rating_val <= 5:
                progress_record.rating = rating_val

        progress_record.save()
        status_val = progress_record.status
        msg = f"Updated '{resource.title}' status to {progress_record.get_status_display()}!"

    # Return JSON for AJAX requests
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({
            "success": True,
            "message": msg,
            "resource_id": resource.id,
            "status": status_val,
        })

    messages.success(request, msg)
    allowed_views = {
        "overview",
        "my-learning",
        "skill-recommendations",
        "learning-resources",
        "learning-progress",
    }
    next_view = request.POST.get("next", "")
    open_skill = request.POST.get("open_skill", "")
    target = reverse("dashboard")
    if open_skill.isdigit():
        target = f"{target}?skill={open_skill}"
    if next_view in allowed_views:
        target = f"{target}#{next_view}"
    return redirect(target)


# ==========================================
# REST / JSON API ENDPOINTS
# ==========================================

@login_required
@require_GET
def api_recommendations(request):
    """JSON API endpoint returning personalized ML skill recommendations for the logged-in student."""
    profile = StudentProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({"error": "Profile not found"}, status=404)

    top_n = int(request.GET.get("top_n", 6))
    rec_data = get_recommendations_for_student(profile, top_n=top_n)

    skills_json = [
        {
            "skill_id": s.skill_id,
            "skill_name": s.skill_name,
            "category": s.category,
            "description": s.description,
            "match_score": s.match_score,
            "match_percentage": s.match_percentage,
            "match_reasons": s.match_reasons,
            "top_terms": s.top_contributing_terms,
            "resources": s.resources,
        }
        for s in rec_data["recommended_skills"]
    ]

    return JsonResponse({
        "student": {
            "username": request.user.username,
            "full_name": profile.full_name,
            "course": profile.course,
            "year_of_study": profile.year_of_study,
            "interests": profile.get_interests_list(),
        },
        "engine_version": rec_data["engine_version"],
        "recommended_skills": skills_json,
        "recommended_resources": rec_data["recommended_resources"],
    })


@require_GET
def api_resources(request):
    """
    JSON API endpoint for searching and filtering learning resources.
    Filters: skill_id, category, difficulty, type, q (search query).
    """
    qs = LearningResource.objects.filter(is_active=True).select_related("skill")

    skill_id = request.GET.get("skill_id")
    if skill_id and skill_id.isdigit():
        qs = qs.filter(skill_id=int(skill_id))

    category = request.GET.get("category")
    if category:
        qs = qs.filter(skill__category__iexact=category)

    difficulty = request.GET.get("difficulty")
    if difficulty:
        qs = qs.filter(difficulty__iexact=difficulty)

    res_type = request.GET.get("type")
    if res_type:
        qs = qs.filter(resource_type__iexact=res_type)

    query = request.GET.get("q")
    if query:
        qs = qs.filter(title__icontains=query) | qs.filter(description__icontains=query)

    resources_data = [
        {
            "id": r.id,
            "title": r.title,
            "skill": r.skill.name,
            "category": r.skill.category,
            "platform": r.platform,
            "resource_type": r.get_resource_type_display(),
            "difficulty": r.get_difficulty_display(),
            "url": r.url,
            "description": r.description,
        }
        for r in qs
    ]

    return JsonResponse({
        "count": len(resources_data),
        "results": resources_data,
    })


@login_required
@require_GET
def api_my_progress(request):
    """JSON API endpoint returning the student's saved, in-progress, and completed resources."""
    profile = StudentProfile.objects.filter(user=request.user).first()
    if not profile:
        return JsonResponse({"error": "Profile not found"}, status=404)

    records = StudentResourceProgress.objects.filter(profile=profile).select_related("resource", "resource__skill")

    progress_data = [
        {
            "resource_id": p.resource.id,
            "title": p.resource.title,
            "skill": p.resource.skill.name,
            "status": p.status,
            "status_display": p.get_status_display(),
            "rating": p.rating,
            "url": p.resource.url,
            "updated_at": p.updated_at.isoformat(),
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        }
        for p in records
    ]

    return JsonResponse({
        "total_records": len(progress_data),
        "completed_count": sum(1 for p in progress_data if p["status"] == "completed"),
        "in_progress_count": sum(1 for p in progress_data if p["status"] == "in_progress"),
        "saved_count": sum(1 for p in progress_data if p["status"] == "saved"),
        "records": progress_data,
    })