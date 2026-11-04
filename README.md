# Skillmatch

Skillmatch is the Django app in the `ML Project` folder.

## Run

From the repository root:

```powershell
python -m pip install -r ".\ML Project\requirements.txt"
Push-Location ".\ML Project"
python manage.py migrate
python manage.py seed_data
python manage.py train_recommender
python manage.py runserver 127.0.0.1:8000
```

The site opens at http://127.0.0.1:8000/.

In VS Code, run the **Skillmatch** task (Terminal > Run Task) or start the **Skillmatch** launch configuration. Both start the Django app in `ML Project`.

## Deploy (PythonAnywhere)

Local `runserver` stays in debug mode. On PythonAnywhere the app turns production mode on by itself.

After pulling `main`:

```bash
cd "/home/thagajunnisha/Machine-Learning/ML Project"
python manage.py migrate
python manage.py seed_data
python manage.py train_recommender
python manage.py collectstatic --noinput
```

Then in the PythonAnywhere Web tab:

1. Source code: `/home/thagajunnisha/Machine-Learning/ML Project`
2. WSGI file: paste `ML Project/config/pythonanywhere_wsgi.py`
3. Static files: URL `/static/` → directory `/home/thagajunnisha/Machine-Learning/ML Project/staticfiles`
4. Reload the site

Change `PROJECT_HOME` in the WSGI file if the clone path is different.

## Deploy (Vercel)

Local `runserver` still uses SQLite. Vercel cannot keep that file, so Skillmatch uses Vercel Postgres there and leaves local data alone.

Import `thahajnisha95-rgb/Machine-Learning` on Rasheeda's Vercel account with:

1. Root Directory: `ML Project` (not the repo root)
2. Storage: add Postgres. Vercel sets `DATABASE_URL`
3. Environment variable: `DJANGO_SECRET_KEY` (a long random value)
4. Deploy from `main`

Vercel turns production mode on by itself, collects static files, then runs migrate, seed, and the recommender train during the build.
