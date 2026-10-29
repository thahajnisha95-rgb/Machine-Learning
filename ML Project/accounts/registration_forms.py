import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class StudentRegistrationForm(UserCreationForm):
    username = forms.RegexField(
        regex=r"^[A-Za-z0-9]{10}$",
        min_length=10,
        max_length=10,
        label="Username",
        help_text="Use exactly 10 letters or numbers, with no special characters.",
        error_messages={
            "invalid": "Username must be exactly 10 letters or numbers, with no special characters.",
        },
        widget=forms.TextInput(attrs={
            "autocomplete": "username",
            "autofocus": True,
            "class": "auth-input",
            "maxlength": "10",
            "placeholder": "10 letters or numbers",
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({
            "autocomplete": "new-password",
            "class": "auth-input",
            "placeholder": "At least 8 characters",
        })
        self.fields["password1"].help_text = (
            "Use at least 8 characters and include at least one special character."
        )
        self.fields["password1"].validators.append(self.validate_special_character)
        self.fields["password2"].widget.attrs.update({
            "autocomplete": "new-password",
            "class": "auth-input",
            "placeholder": "Enter your password again",
        })

    @staticmethod
    def validate_special_character(password):
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                "Password must include at least one special character.",
                code="missing_special_character",
            )
