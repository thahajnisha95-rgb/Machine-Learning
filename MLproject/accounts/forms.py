import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudentProfile


THREE_YEAR_CHOICES = [
    (1, "First Year"),
    (2, "Second Year"),
    (3, "Final Year"),
]
FOUR_YEAR_CHOICES = [
    (1, "First Year"),
    (2, "Second Year"),
    (3, "Third Year"),
    (4, "Final Year"),
]


def course_year_choices(course):
    """Return four year options for engineering degrees, three for other courses."""
    normalized_course = (course or "").lower().replace(".", "").strip()
    is_four_year_course = (
        re.search(r"\bb\s*tech\b", normalized_course)
        or re.search(r"\bb\s*e\b", normalized_course)
        or "bachelor of technology" in normalized_course
        or "bachelor of engineering" in normalized_course
    )
    return FOUR_YEAR_CHOICES if is_four_year_course else THREE_YEAR_CHOICES


class StudentRegistrationForm(UserCreationForm):
    """Custom registration form: username = letters & digits only, max 100 chars."""

    username = forms.CharField(
        max_length=100,
        help_text="",   # clear the default help text
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Enter your username",
            "autocomplete": "username",
        }),
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Create a password",
            "id": "id_password1",
            "autocomplete": "new-password",
        }),
    )

    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Confirm your password",
            "id": "id_password2",
            "autocomplete": "new-password",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise forms.ValidationError(
                "Username may only contain letters and numbers."
            )
        if len(username) > 100:
            raise forms.ValidationError(
                "Username must be 100 characters or fewer."
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username



class StudentProfileForm(forms.ModelForm):
    year_of_study = forms.ChoiceField(
        choices=THREE_YEAR_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Year of Study",
        help_text=(
            "Three-year courses use First, Second, and Final Year. "
            "B.Tech and B.E. courses also include Third Year."
        )
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
                "placeholder": "Type or choose a degree / department",
                "list": "course-options",
                "autocomplete": "off",
            }),
            "interests": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "e.g. Python, Machine Learning, Deep Learning, SQL, React"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        course = self.data.get("course") if self.is_bound else self.initial.get("course")
        if not course and self.instance.pk:
            course = self.instance.course
        self.fields["year_of_study"].choices = course_year_choices(course)

    def clean_year_of_study(self):
        val = self.cleaned_data.get("year_of_study")
        try:
            return int(val)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please provide a valid year.")
