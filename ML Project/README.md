# ML Project

This directory was prepared from the archive `MLproject.zip` in the repository root.

The archive appears to contain a Django / machine-learning project with the following structure:

- `accounts/`
  - `__init__.py`
  - `admin.py`
  - `forms.py`
  - `models.py`
  - `tests.py`
  - `urls.py`
  - `views.py`
  - `management/commands/seed_data.py`
  - `management/commands/train_recommender.py`
  - `migrations/0001_initial.py`
  - `migrations/0002_skill_learningresource.py`
  - `templates/accounts/dashboard.html`
  - `templates/accounts/login.html`
  - `templates/accounts/profile_form.html`
  - `templates/accounts/register.html`
- `config/`
  - `asgi.py`
  - `settings.py`
  - `urls.py`
  - `wsgi.py`
- `requirements.txt`
- `recommender_model.json`
- `student_learning_system.py`

Note: the original archive is still present at the repository root as `MLproject.zip`.
This folder is the extracted project directory created in the repository for organization and access.

## Run locally

From the repository root, install the pinned dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r ".\ML Project\requirements.txt"
```

Then initialize the database and start the Django app:

```powershell
Push-Location ".\ML Project"
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py seed_data
..\.venv\Scripts\python.exe manage.py train_recommender
..\.venv\Scripts\python.exe manage.py runserver
```

The seed command adds the curated skill tracks and learning resources required by the recommendation engine. Run it after migrations on a new database. It is safe to run again.

The dashboard uses the local recommendation engine. Its JSON endpoints are available at `/api/recommendations/` (requires login) and `/api/resources/`.
