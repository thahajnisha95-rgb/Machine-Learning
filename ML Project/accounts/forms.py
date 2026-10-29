from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import StudentProfile


class StyledAuthenticationForm(AuthenticationForm):
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
    YEAR_CHOICES = [
        (1, "1st Year (Freshman)"),
        (2, "2nd Year (Sophomore)"),
        (3, "3rd Year (Junior)"),
        (4, "4th Year (Senior)"),
        (5, "Postgraduate / Master's"),
    ]

    year_of_study = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Year of Study",
        help_text="Select your current year of study"
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

    def clean_year_of_study(self):
        val = self.cleaned_data.get("year_of_study")
        try:
            return int(val)
        except (ValueError, TypeError):
            raise forms.ValidationError("Please provide a valid year.")
