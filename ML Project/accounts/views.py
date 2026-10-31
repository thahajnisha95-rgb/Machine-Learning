from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import StudentProfile, Skill, LearningResource, StudentResourceProgress
from .forms import StudentProfileForm
from .registration_forms import StudentRegistrationForm
from student_learning_system import get_recommendations_for_student


FALLBACK_SKILLS = [
    {
        "name": "Python Programming",
        "category": "Programming Languages",
        "description": "A practical starting language for coursework, data work, and the projects behind many AI tools.",
    },
    {
        "name": "Machine Learning",
        "category": "Artificial Intelligence",
        "description": "Methods that learn patterns from data, from first models through evaluation you can explain.",
    },
    {
        "name": "Deep Learning & Neural Networks",
        "category": "Artificial Intelligence",
        "description": "Layered models for images, text, and other complex data, introduced at a pace that matches your year.",
    },
    {
        "name": "Web Development & Django",
        "category": "Web Development",
        "description": "Pages, forms, and data-backed applications, including the kind of site you are using now.",
    },
    {
        "name": "Computer Vision",
        "category": "Artificial Intelligence",
        "description": "Working with images and video so a model can detect, classify, and describe what it sees.",
    },
]


SURVEY_STEPS = [
    {
        "key": "name",
        "number": 1,
        "kicker": "Welcome",
        "title": "May we start with the name you like to be called?",
        "help": "A first name is perfectly fine. This is how Skillmatch will greet you.",
    },
    {
        "key": "course",
        "number": 2,
        "kicker": "Your course",
        "title": "What are you studying at the moment?",
        "help": "Your degree or programme is enough, such as B.Tech Computer Science or BCA.",
    },
    {
        "key": "year",
        "number": 3,
        "kicker": "Your year",
        "title": "How far along are you in that course?",
        "help": "We use this so the courses we suggest sit at a comfortable difficulty.",
    },
    {
        "key": "interests",
        "number": 4,
        "kicker": "Your interests",
        "title": "Which skills would you like us to match for you?",
        "help": "Pick as many as you like. These are what we use to find skills and courses.",
    },
    {
        "key": "goal",
        "number": 5,
        "kicker": "Your goal",
        "title": "What would you like help with first?",
        "help": "Choose the aim that feels closest. We will pair it with your interests.",
    },
]

SURVEY_READY_STEP = len(SURVEY_STEPS) + 1

SURVEY_YEAR_CHOICES = [
    (1, "1st year"),
    (2, "2nd year"),
    (3, "3rd year"),
    (4, "4th year"),
    (5, "Postgraduate / Master's"),
]

SURVEY_GOALS = [
    "Become more confident in programming",
    "Get ready for internships and placements",
    "Build projects I can show",
    "Explore AI, data, and machine learning",
    "Do better in my current coursework",
]

SURVEY_COURSE_HINTS = [
    "B.Tech Computer Science",
    "B.Sc Artificial Intelligence",
    "BCA",
    "B.Sc Data Science",
    "M.Sc AI",
    "MCA",
]

SURVEY_INTEREST_EXTRAS = [
    "Python",
    "Java",
    "JavaScript",
    "HTML",
    "CSS",
    "React",
    "Next.js",
    "Django",
    "SQL",
    "Bootstrap",
    "Machine Learning",
    "Deep Learning",
    "Data Science",
    "NLP",
    "Web Development",
    "Cloud",
]


def _skill_chart_label(name: str) -> str:
    """Short legend label for the dashboard donut, without changing skill records."""
    open_at = name.find("(")
    close_at = name.find(")", open_at + 1)
    if open_at != -1 and close_at > open_at:
        inner = name[open_at + 1:close_at].strip()
        if inner:
            return inner
    short = name.split(" & ", 1)[0]
    if short.endswith(" Programming"):
        short = short[: -len(" Programming")]
    return short.strip() or name


def _ensure_student_profile(user):
    profile, _created = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            "full_name": user.username,
            "course": "",
            "year_of_study": 1,
            "interests": "",
            "learning_goal": "",
            "onboarding_complete": False,
        },
    )
    return profile


def user_needs_onboarding(user):
    if not getattr(user, "is_authenticated", False):
        return False
    profile = StudentProfile.objects.filter(user=user).first()
    if profile is None:
        return True
    return profile.needs_onboarding()


def post_login_destination(user):
    if user_needs_onboarding(user):
        return "onboarding"
    return "dashboard"


class SkillmatchLoginView(LoginView):
    """Send new or incomplete profiles to the survey instead of the dashboard."""

    def get_success_url(self):
        if user_needs_onboarding(self.request.user):
            return reverse("onboarding")
        return super().get_success_url()


def csrf_failure(request, reason=""):
    """Reload the form with a fresh token instead of Django's debug 403 page."""
    messages.warning(
        request,
        "Please try again. That form expired, so nothing was submitted.",
    )
    path = request.path or ""
    if path.startswith(reverse("register")):
        return redirect("register")
    if path.startswith(reverse("onboarding")):
        return redirect("onboarding")
    if path.startswith(reverse("edit_profile")):
        return redirect("edit_profile")
    return redirect("login")


def require_complete_profile(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if user_needs_onboarding(request.user):
            return redirect("onboarding")
        return view_func(request, *args, **kwargs)
    return wrapped


def survey_interest_options():
    labels = []
    seen = set()
    for skill in Skill.objects.order_by("name"):
        label = _skill_chart_label(skill.name)
        key = label.lower()
        if label and key not in seen:
            labels.append(label)
            seen.add(key)
    for extra in SURVEY_INTEREST_EXTRAS:
        key = extra.lower()
        if key not in seen:
            labels.append(extra)
            seen.add(key)
    if not labels:
        for skill in FALLBACK_SKILLS:
            labels.append(_skill_chart_label(skill["name"]))
    return labels


def marketing_home(request):
    """Public product page. Sign-in continues through the existing login flow."""
    skills = list(
        Skill.objects.exclude(name__icontains="Data Science")
        .values("name", "category", "description")[:6]
    )
    if not skills:
        skills = list(FALLBACK_SKILLS)
    else:
        seen = {skill["name"] for skill in skills}
        for extra in FALLBACK_SKILLS:
            if len(skills) >= 6:
                break
            if extra["name"] not in seen:
                skills.append(extra)
                seen.add(extra["name"])
    return render(
        request,
        "accounts/marketing.html",
        {"skills": skills},
    )


def register(request):
    """Register a new student account and automatically provision a student profile."""
    if request.user.is_authenticated:
        return redirect(post_login_destination(request.user))

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
                    "learning_goal": "",
                    "onboarding_complete": False,
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
def onboarding(request):
    """One-question survey that fills the student profile before the app opens."""
    profile = _ensure_student_profile(request.user)
    just_finished = request.session.get("onboarding_just_finished")
    if not profile.needs_onboarding() and not just_finished:
        return redirect("dashboard")

    total_questions = len(SURVEY_STEPS)
    try:
        reached = int(request.session.get("onboarding_reached") or 1)
    except (TypeError, ValueError):
        reached = 1
    reached = max(1, min(reached, SURVEY_READY_STEP))
    try:
        step = int(request.GET.get("step") or request.POST.get("step") or 1)
    except (TypeError, ValueError):
        step = 1
    if just_finished:
        step = SURVEY_READY_STEP
    else:
        step = max(1, min(step, total_questions, max(1, reached)))

    error = ""
    if request.method == "POST":
        action = request.POST.get("action") or "next"
        if action == "open_app":
            if profile.needs_onboarding():
                return redirect("onboarding")
            if not profile.onboarding_complete:
                profile.onboarding_complete = True
                profile.save(update_fields=["onboarding_complete"])
            request.session.pop("onboarding_just_finished", None)
            request.session.pop("onboarding_reached", None)
            return redirect("dashboard")
        if action == "back":
            return redirect(f"{reverse('onboarding')}?step={max(1, step - 1)}")

        if step == 1:
            name = (request.POST.get("full_name") or "").strip()
            if not name:
                error = "Please share the name you would like us to use."
            elif len(name) > 100:
                error = "Please keep that name within 100 characters."
            else:
                profile.full_name = name
                profile.save(update_fields=["full_name"])
                request.session["onboarding_reached"] = max(reached, 2)
                return redirect(f"{reverse('onboarding')}?step=2")
        elif step == 2:
            course = (request.POST.get("course") or "").strip()
            if not course:
                error = "Please tell us the course or degree you are studying."
            elif len(course) > 100:
                error = "Please keep the course name within 100 characters."
            else:
                profile.course = course
                profile.save(update_fields=["course"])
                request.session["onboarding_reached"] = max(reached, 3)
                return redirect(f"{reverse('onboarding')}?step=3")
        elif step == 3:
            try:
                year = int(request.POST.get("year_of_study") or 0)
            except (TypeError, ValueError):
                year = 0
            valid_years = {choice[0] for choice in SURVEY_YEAR_CHOICES}
            if year not in valid_years:
                error = "Please choose the year that fits you best."
            else:
                profile.year_of_study = year
                profile.save(update_fields=["year_of_study"])
                request.session["onboarding_reached"] = max(reached, 4)
                return redirect(f"{reverse('onboarding')}?step=4")
        elif step == 4:
            picked = [item.strip() for item in request.POST.getlist("interest") if item.strip()]
            extra = (request.POST.get("interest_extra") or "").strip()
            if extra:
                picked.extend(
                    part.strip()
                    for part in extra.replace(";", ",").split(",")
                    if part.strip()
                )
            unique = []
            seen = set()
            for item in picked:
                key = item.lower()
                if key not in seen:
                    unique.append(item)
                    seen.add(key)
            if not unique:
                error = "Please pick at least one interest so we can match skills and courses."
            else:
                profile.interests = ", ".join(unique)
                profile.save(update_fields=["interests"])
                request.session["onboarding_reached"] = max(reached, 5)
                return redirect(f"{reverse('onboarding')}?step=5")
        elif step == 5:
            goal = (request.POST.get("learning_goal") or "").strip()
            if goal not in SURVEY_GOALS:
                error = "Please choose the aim that feels closest for now."
            else:
                profile.learning_goal = goal
                profile.onboarding_complete = True
                profile.save(update_fields=["learning_goal", "onboarding_complete"])
                request.session["onboarding_just_finished"] = True
                request.session["onboarding_reached"] = SURVEY_READY_STEP
                return redirect(f"{reverse('onboarding')}?step={SURVEY_READY_STEP}")

    step_meta = SURVEY_STEPS[step - 1] if 1 <= step <= total_questions else None
    posted = {
        "full_name": "",
        "course": "",
        "year": "",
        "interests": set(),
        "interest_extra": "",
        "goal": "",
    }
    if error:
        posted = {
            "full_name": request.POST.get("full_name", ""),
            "course": request.POST.get("course", ""),
            "year": request.POST.get("year_of_study", ""),
            "interests": {item.strip().lower() for item in request.POST.getlist("interest") if item.strip()},
            "interest_extra": request.POST.get("interest_extra", ""),
            "goal": request.POST.get("learning_goal", ""),
        }
    return render(
        request,
        "accounts/onboarding.html",
        {
            "profile": profile,
            "step": step,
            "total_questions": total_questions,
            "step_meta": step_meta,
            "error": error,
            "year_choices": SURVEY_YEAR_CHOICES,
            "course_hints": SURVEY_COURSE_HINTS,
            "interest_options": survey_interest_options(),
            "posted": posted,
            "goal_choices": SURVEY_GOALS,
            "is_ready": step == SURVEY_READY_STEP,
            "progress_ticks": range(1, total_questions + 1),
        },
    )


@login_required
@require_complete_profile
def dashboard(request):
    """Main student dashboard displaying profile, ML recommendations, and progress tracking."""
    profile = StudentProfile.objects.filter(user=request.user).first()

    recommendation_data = None
    if profile:
        recommendation_data = get_recommendations_for_student(profile, top_n=6)
        for rec in recommendation_data.get("recommended_skills") or []:
            rec.chart_label = _skill_chart_label(rec.skill_name)

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
@require_complete_profile
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
@require_complete_profile
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
@require_complete_profile
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