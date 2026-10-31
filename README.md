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
