import json
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from .models import StudentProfile


COURSE_OPTIONS = (
    "BSc Computer Science",
    "BSc Data Science",
    "BSc Information Technology",
    "BSc Mathematics",
    "BSc Physics",
    "BSc Chemistry",
    "BSc Biology",
    "BSc Biotechnology",
    "BSc Statistics",
    "BSc Artificial Intelligence",
    "BSc Electronics",
    "BSc Nursing",
    "BSc Agriculture",
    "BSc Psychology",
    "BTech Computer Science",
    "BTech Artificial Intelligence and Data Science",
    "BTech Information Technology",
    "BTech Electronics and Communication",
    "BTech Mechanical Engineering",
    "BTech Civil Engineering",
    "BTech Electrical Engineering",
    "BTech Biotechnology",
    "BTech Cyber Security",
    "BE Computer Science",
    "BE Information Technology",
    "BE Mechanical Engineering",
    "BE Civil Engineering",
    "BE Electrical Engineering",
    "BE Electronics and Communication",
    "BCA",
    "BCA Data Science",
    "BCA Cloud Computing",
    "BCA Cyber Security",
    "BCA Artificial Intelligence",
    "BA English",
    "BA Economics",
    "BA Psychology",
    "BA History",
    "BA Political Science",
    "BCom General",
    "BCom Accounting and Finance",
    "BCom Computer Applications",
    "BBA",
    "BBA Finance",
    "BBA Marketing",
    "BBA Business Analytics",
    "MSc Computer Science",
    "MSc Data Science",
    "MSc Artificial Intelligence",
    "MSc Mathematics",
    "MSc Physics",
    "MCA",
    "MCA Data Science",
    "MCA Artificial Intelligence",
    "MBA",
    "MBA Finance",
    "MBA Marketing",
    "MBA Business Analytics",
    "MTech Computer Science",
    "MTech Artificial Intelligence",
    "MTech Information Technology",
    "MA English",
    "MA Economics",
    "MA Psychology",
    "MCom",
)

COURSE_DURATION_RULES = {
    "bachelorofscience": 3,
    "bsc": 3,
    "bachelorofcomputerapplications": 3,
    "bca": 3,
    "bachelorofarts": 3,
    "ba": 3,
    "bachelorofcommerce": 3,
    "bcom": 3,
    "bachelorofbusinessadministration": 3,
    "bba": 3,
    "bsw": 3,
    "bhm": 3,
    "bacheloroftechnology": 4,
    "btech": 4,
    "bachelorofengineering": 4,
    "beng": 4,
    "be": 4,
}


def get_course_year_count(course):
    normalized_course = re.sub(r"[^a-z0-9]", "", (course or "").casefold())
    for prefix in sorted(COURSE_DURATION_RULES, key=len, reverse=True):
        if normalized_course.startswith(prefix):
            return COURSE_DURATION_RULES[prefix]
    if normalized_course.startswith(("m", "pg", "postgraduate")):
        return 2
    return 4


def get_year_choices(year_count):
    labels = {
        2: ("First Year", "Final Year"),
        3: ("First Year", "Second Year", "Final Year"),
        4: ("First Year", "Second Year", "Third Year", "Final Year"),
    }
    return tuple((year, label) for year, label in enumerate(labels[year_count], start=1))


class StyledAuthenticationForm(AuthenticationForm):
    """Built-in login form with placeholder attrs for the new login page."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "auth-input",
            "placeholder": "Enter your username",
            "autocomplete": "username",
            "spellcheck": "false",
        })
        self.fields["password"].widget.attrs.update({
            "class": "auth-input",
            "placeholder": "Enter your password",
            "autocomplete": "current-password",
        })


class StudentProfileForm(forms.ModelForm):
    year_of_study = forms.ChoiceField(
        choices=get_year_choices(4),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Year of Study",
        help_text="Select your current year of study"
    )
    username = forms.CharField(
        max_length=150,
        label="Username",
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autocomplete": "username",
            "spellcheck": "false",
        }),
    )

    class Meta:
        model = StudentProfile
        fields = [
            "full_name",
            "course",
            "year_of_study",
            "interests",
        ]
        labels = {
            "full_name": "Full Name",
            "course": "Degree / Course",
            "interests": "Interests & Technologies",
        }
        help_texts = {
            "full_name": "Your legal or preferred display name",
            "course": "e.g. B.Sc. Computer Science, AI & Data Science, BCA, B.Tech IT",
            "interests": "Enter topics or tools you are interested in, separated by commas (e.g., Python, Machine Learning, Web Development, Cloud)",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Alex Johnson"
            }),
            "course": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. B.Sc Artificial Intelligence"
            }),
            "interests": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "e.g. Python, Machine Learning, Deep Learning, SQL, React"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(self.instance, "user", None)
        if getattr(user, "pk", None) and not self.is_bound:
            self.initial["username"] = user.username
        course_value = self.data.get(
            self.add_prefix("course"),
            self.initial.get("course", getattr(self.instance, "course", "")),
        )
        self.course_options = COURSE_OPTIONS
        self.fields["course"].widget.attrs.update({"list": "course-options"})
        self.fields["year_of_study"].choices = get_year_choices(
            get_course_year_count(course_value)
        )
        self.fields["year_of_study"].widget.attrs["data-course-durations"] = json.dumps(
            COURSE_DURATION_RULES
        )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise forms.ValidationError("Enter a username.")
        taken = User.objects.filter(username__iexact=username)
        user = getattr(self.instance, "user", None)
        if getattr(user, "pk", None):
            taken = taken.exclude(pk=user.pk)
        if taken.exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_year_of_study(self):
        val = self.cleaned_data.get("year_of_study")
        try:
            return int(val)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please provide a valid year.")

    def save(self, commit=True):
        profile = super().save(commit=commit)
        username = self.cleaned_data.get("username")
        user = getattr(profile, "user", None)
        if user is not None and username and user.username != username:
            user.username = username
            if commit:
                user.save(update_fields=["username"])
        return profile
