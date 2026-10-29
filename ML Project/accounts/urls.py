from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from . import views

try:
    from .forms import StyledAuthenticationForm as LoginForm
except ImportError:
    LoginForm = AuthenticationForm

urlpatterns = [
    path("", views.marketing_home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("progress/<int:resource_id>/toggle/", views.toggle_resource_progress, name="toggle_resource_progress"),

    # REST / JSON API Routes
    path("api/recommendations/", views.api_recommendations, name="api_recommendations"),
    path("api/resources/", views.api_resources, name="api_resources"),
    path("api/my-progress/", views.api_my_progress, name="api_my_progress"),

    # Authentication
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(http_method_names=["get", "post", "options"]),
        name="logout",
    ),
]