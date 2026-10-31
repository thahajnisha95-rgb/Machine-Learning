from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.management import call_command

from accounts.models import StudentProfile, Skill, LearningResource, StudentResourceProgress
from accounts.forms import StudentProfileForm
from student_learning_system import (
    clean_and_tokenize,
    compute_text_similarity,
    get_recommendations_for_student,
    TFIDFVectorizer,
)


class AccessPermissionTests(TestCase):
    """Test access permissions and authentication redirects."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="student1", password="password123")
        self.profile = StudentProfile.objects.create(
            user=self.user,
            full_name="Student One",
            course="Computer Science",
            year_of_study=2,
            interests="Python, Django",
            onboarding_complete=True,
        )

    def test_home_is_public_marketing_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")
        self.assertContains(response, "Skillmatch")
        self.assertContains(response, reverse("login"))
        self.assertContains(response, reverse("register"))

    def test_unauthenticated_dashboard_redirects(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_unauthenticated_edit_profile_redirects(self):
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_dashboard_access(self):
        self.client.login(username="student1", password="password123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello, student1")
        self.assertNotContains(response, "Good morning")
        self.assertContains(response, "Student One")
        self.assertContains(response, "Computer Science")

    def test_dashboard_lists_all_active_resources_and_only_breadcrumb_heading(self):
        python = Skill.objects.create(
            name="Python Programming",
            category="Programming Languages",
            keywords="python",
        )
        machine_learning = Skill.objects.create(
            name="Machine Learning",
            category="Artificial Intelligence",
            keywords="machine learning",
        )
        LearningResource.objects.create(
            skill=python,
            title="Python Course",
            url="https://example.com/python",
        )
        LearningResource.objects.create(
            skill=machine_learning,
            title="Machine Learning Course",
            url="https://example.com/ml",
        )
        for resource_number in range(1, 5):
            LearningResource.objects.create(
                skill=python,
                title=f"Additional Python Resource {resource_number}",
                url=f"https://example.com/python-{resource_number}",
            )
        LearningResource.objects.create(
            skill=machine_learning,
            title="Inactive Course",
            url="https://example.com/inactive",
            is_active=False,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["learning_resources"]), 6)
        self.assertContains(response, 'class="preview-row"', count=6)
        self.assertContains(response, "Python Course")
        self.assertContains(response, "Machine Learning Course")
        self.assertContains(response, "Additional Python Resource 4")
        self.assertContains(response, 'data-category="Artificial Intelligence"')
        self.assertNotContains(response, "Inactive Course")
        self.assertContains(response, '<li id="crumb-current" aria-current="page">Dashboard</li>')
        self.assertNotContains(response, 'id="page-title"')
        self.assertContains(response, 'id="sidebar-collapse"')
        self.assertNotContains(response, '<span class="nav-label">Collapse sidebar</span>')

    def test_authenticated_edit_profile_access(self):
        self.client.login(username="student1", password="password123")
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Profile")
        self.assertContains(response, '<datalist id="course-options">')
        self.assertContains(response, "BSc Computer Science")


class StudentProfileTests(TestCase):
    """Test Student Profile model, form, and database updates."""

    def setUp(self):
        self.user = User.objects.create_user(username="john_doe", password="SecurePassword123!")

    def test_profile_creation_and_interests_list(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            full_name="John Doe",
            course="B.Sc Artificial Intelligence",
            year_of_study=3,
            interests="Machine Learning, Deep Learning; Computer Vision",
        )
        interests = profile.get_interests_list()
        self.assertEqual(len(interests), 3)
        self.assertIn("Machine Learning", interests)
        self.assertIn("Deep Learning", interests)
        self.assertIn("Computer Vision", interests)

    def test_profile_form_validation(self):
        form_data = {
            "full_name": "Jane Smith",
            "username": "jane_smith",
            "course": "BCA Data Science",
            "year_of_study": 2,
            "interests": "Python, SQL, Tableau",
        }
        form = StudentProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_profile_form_year_choices_match_course_duration(self):
        cases = (
            ("B.Sc. Computer Science", 3, ("First Year", "Second Year", "Final Year")),
            ("BCA Data Science", 3, ("First Year", "Second Year", "Final Year")),
            ("B.Tech. Computer Science", 4, ("First Year", "Second Year", "Third Year", "Final Year")),
            ("B.E. Civil Engineering", 4, ("First Year", "Second Year", "Third Year", "Final Year")),
            ("M.Sc. Data Science", 2, ("First Year", "Final Year")),
            ("MCA", 2, ("First Year", "Final Year")),
        )
        for course, year_count, expected_labels in cases:
            with self.subTest(course=course):
                form = StudentProfileForm(data={
                    "full_name": "Jane Smith",
                    "course": course,
                    "year_of_study": year_count,
                    "interests": "Python",
                })
                self.assertEqual(
                    tuple(label for _, label in form.fields["year_of_study"].choices),
                    expected_labels,
                )
                self.assertTrue(form.is_valid(), form.errors)

    def test_profile_form_rejects_year_outside_course_duration(self):
        form = StudentProfileForm(data={
            "full_name": "Jane Smith",
            "course": "BCA Data Science",
            "year_of_study": 4,
            "interests": "Python",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("year_of_study", form.errors)

    def test_profile_edit_view_post_updates_database(self):
        client = Client()
        client.login(username="john_doe", password="SecurePassword123!")

        post_data = {
            "full_name": "John Doe Updated",
            "username": "john_updated",
            "course": "M.Sc AI & Robotics",
            "year_of_study": 2,
            "interests": "Robotics, ROS, Python",
        }
        response = client.post(reverse("edit_profile"), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        profile = StudentProfile.objects.get(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(profile.full_name, "John Doe Updated")
        self.assertEqual(self.user.username, "john_updated")
        self.assertEqual(profile.course, "M.Sc AI & Robotics")
        self.assertEqual(profile.year_of_study, 2)
        self.assertIn("Robotics", profile.interests)


class LearningResourceAndProgressTests(TestCase):
    """Test Skill, LearningResource, and StudentResourceProgress tracking."""

    def setUp(self):
        self.user = User.objects.create_user(username="tracker_user", password="password123")
        self.profile = StudentProfile.objects.create(
            user=self.user,
            full_name="Tracker User",
            course="Information Technology",
            year_of_study=2,
            interests="Cloud, DevOps",
            onboarding_complete=True,
        )
        self.skill = Skill.objects.create(
            name="Cloud Computing",
            category="Infrastructure",
            keywords="aws, azure, gcp, docker",
            description="Cloud platforms and containerization.",
        )
        self.resource = LearningResource.objects.create(
            skill=self.skill,
            title="AWS Cloud Essentials",
            platform="AWS",
            resource_type="course",
            difficulty="beginner",
            url="https://example.com/aws",
            is_active=True,
        )

    def test_toggle_progress_to_in_progress_and_completed(self):
        client = Client()
        client.login(username="tracker_user", password="password123")

        # Mark in_progress
        response = client.post(
            reverse("toggle_resource_progress", args=[self.resource.id]),
            {"status": "in_progress"},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        progress = StudentResourceProgress.objects.get(profile=self.profile, resource=self.resource)
        self.assertEqual(progress.status, "in_progress")

        # Mark completed with rating
        response = client.post(
            reverse("toggle_resource_progress", args=[self.resource.id]),
            {"status": "completed", "rating": "5"},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        progress.refresh_from_db()
        self.assertEqual(progress.status, "completed")
        self.assertEqual(progress.rating, 5)
        self.assertIsNotNone(progress.completed_at)

        # Remove from tracker
        response = client.post(
            reverse("toggle_resource_progress", args=[self.resource.id]),
            {"status": "remove"},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StudentResourceProgress.objects.filter(profile=self.profile, resource=self.resource).exists())


class JSONAPITests(TestCase):
    """Test REST / JSON API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(username="api_user", password="password123")
        self.profile = StudentProfile.objects.create(
            user=self.user,
            full_name="API User",
            course="Computer Engineering",
            year_of_study=3,
            interests="Python, Machine Learning",
            onboarding_complete=True,
        )
        self.skill = Skill.objects.create(
            name="Machine Learning",
            category="AI",
            keywords="ml, scikit-learn",
            description="ML algorithms",
        )
        self.resource = LearningResource.objects.create(
            skill=self.skill,
            title="Intro to ML",
            platform="Coursera",
            resource_type="course",
            difficulty="beginner",
            url="https://example.com/ml-course",
            is_active=True,
        )
        self.client = Client()
        self.client.login(username="api_user", password="password123")

    def test_api_recommendations(self):
        response = self.client.get(reverse("api_recommendations"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("student", data)
        self.assertIn("recommended_skills", data)
        self.assertIn("engine_version", data)
        self.assertEqual(data["student"]["username"], "api_user")

    def test_api_resources_search_and_filter(self):
        # Search by query
        response = self.client.get(reverse("api_resources") + "?q=Intro")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["title"], "Intro to ML")

        # Filter by difficulty
        response = self.client.get(reverse("api_resources") + "?difficulty=beginner")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["count"], 1)

    def test_api_my_progress(self):
        StudentResourceProgress.objects.create(
            profile=self.profile,
            resource=self.resource,
            status="saved"
        )
        response = self.client.get(reverse("api_my_progress"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_records"], 1)
        self.assertEqual(data["saved_count"], 1)


class TFIDFEngineAndMLTests(TestCase):
    """Test TF-IDF vector space model, cosine similarity, and management commands."""

    def test_tfidf_vectorization_and_cosine_similarity(self):
        corpus = [
            "python programming web development django",
            "machine learning neural networks deep learning artificial intelligence",
            "data science analysis statistics pandas numpy",
        ]
        vectorizer = TFIDFVectorizer()
        vectorizer.fit(corpus)

        self.assertGreater(len(vectorizer.vocabulary), 5)

        # Check vectors
        vec_query = vectorizer.transform("python web backend")
        vec_doc0 = vectorizer.transform(corpus[0])
        vec_doc1 = vectorizer.transform(corpus[1])

        sim0 = vectorizer.cosine_similarity(vec_query, vec_doc0)
        sim1 = vectorizer.cosine_similarity(vec_query, vec_doc1)

        # Query about python/web should match document 0 much higher than document 1
        self.assertGreater(sim0, sim1)
        self.assertGreater(sim0, 0.3)

    def test_train_recommender_command(self):
        # Should execute successfully without error
        call_command("train_recommender")


class OnboardingSurveyTests(TestCase):
    """New students complete a one-question survey before the dashboard opens."""

    def setUp(self):
        self.python = Skill.objects.create(
            name="Python Programming",
            category="Programming Languages",
            keywords="python",
            description="Python for coursework and backend projects.",
        )
        self.ml = Skill.objects.create(
            name="Machine Learning",
            category="Artificial Intelligence",
            keywords="machine learning, ml",
            description="Supervised and unsupervised learning from data.",
        )
        LearningResource.objects.create(
            skill=self.python,
            title="CS50 Python",
            url="https://example.com/cs50-python",
            platform="edX",
            resource_type="course",
            difficulty="beginner",
        )
        LearningResource.objects.create(
            skill=self.ml,
            title="Andrew Ng Machine Learning",
            url="https://example.com/ml-course",
            platform="Coursera",
            resource_type="course",
            difficulty="beginner",
        )

    def _make_incomplete_user(self, username="newstudent"):
        user = User.objects.create_user(username=username, password="Survey@123")
        StudentProfile.objects.create(
            user=user,
            full_name=username,
            course="",
            year_of_study=1,
            interests="",
        )
        return user

    def test_profile_without_course_or_interests_needs_onboarding(self):
        user = self._make_incomplete_user()
        self.assertTrue(user.studentprofile.needs_onboarding())

    def test_complete_profile_skips_onboarding(self):
        user = User.objects.create_user(username="complete1", password="Survey@123")
        StudentProfile.objects.create(
            user=user,
            full_name="Rasheeda Complete",
            course="Btech computer science",
            year_of_study=4,
            interests="Java, python, HTML, CSS, Bootstrap, react, Nextjs",
            onboarding_complete=True,
        )
        self.client.login(username="complete1", password="Survey@123")

        welcome = self.client.get(reverse("onboarding"))
        self.assertRedirects(welcome, reverse("dashboard"))

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Rasheeda Complete")

    def test_filled_profile_still_sees_survey_until_it_is_finished(self):
        user = User.objects.create_user(username="filledusr1", password="Survey@123")
        StudentProfile.objects.create(
            user=user,
            full_name="Rasheeda",
            course="Btech computer science",
            year_of_study=4,
            interests="Java, python, HTML",
            onboarding_complete=False,
        )
        response = self.client.post(reverse("login"), {
            "username": "filledusr1",
            "password": "Survey@123",
        })
        self.assertRedirects(response, reverse("onboarding"))
        survey = self.client.get(reverse("onboarding"))
        self.assertContains(survey, "May we start with the name you like to be called?")
        self.assertContains(survey, "e.g. Alex Johnson")
        self.assertNotContains(survey, "Rasheeda")
        self.assertNotContains(survey, 'value="Rasheeda"')

    def test_login_sends_incomplete_profile_to_survey_not_dashboard(self):
        self._make_incomplete_user("surveyusr1")
        response = self.client.post(reverse("login"), {
            "username": "surveyusr1",
            "password": "Survey@123",
        })
        self.assertRedirects(response, reverse("onboarding"))

    def test_dashboard_and_recommendation_api_are_blocked_until_survey_is_done(self):
        user = self._make_incomplete_user()
        self.client.force_login(user)

        self.assertRedirects(self.client.get(reverse("dashboard")), reverse("onboarding"))
        self.assertRedirects(self.client.get(reverse("api_recommendations")), reverse("onboarding"))

    def test_survey_shows_one_question_and_ignores_skipped_steps(self):
        user = self._make_incomplete_user()
        self.client.force_login(user)

        first = self.client.get(reverse("onboarding"))
        self.assertEqual(first.status_code, 200)
        self.assertContains(first, "May we start with the name you like to be called?")
        self.assertNotContains(first, "What are you studying at the moment?")
        self.assertNotContains(first, "Which skills would you like us to match for you?")
        self.assertContains(first, "1 of 5")

        skipped = self.client.get(reverse("onboarding") + "?step=4")
        self.assertContains(skipped, "May we start with the name you like to be called?")
        self.assertNotContains(skipped, "Which skills would you like us to match for you?")

    def test_survey_then_dashboard_matches_selected_interests(self):
        user = self._make_incomplete_user("matchusr01")
        self.client.force_login(user)

        name = self.client.post(reverse("onboarding"), {
            "step": "1",
            "action": "next",
            "full_name": "Amina Patel",
        })
        self.assertRedirects(name, reverse("onboarding") + "?step=2")

        course_page = self.client.get(reverse("onboarding") + "?step=2")
        self.assertContains(course_page, "What are you studying at the moment?")
        self.assertNotContains(course_page, "May we start with the name you like to be called?")

        course = self.client.post(reverse("onboarding") + "?step=2", {
            "step": "2",
            "action": "next",
            "course": "B.Tech Computer Science",
        })
        self.assertRedirects(course, reverse("onboarding") + "?step=3")

        year = self.client.post(reverse("onboarding") + "?step=3", {
            "step": "3",
            "action": "next",
            "year_of_study": "2",
        })
        self.assertRedirects(year, reverse("onboarding") + "?step=4")

        interests_page = self.client.get(reverse("onboarding") + "?step=4")
        self.assertContains(interests_page, "Which skills would you like us to match for you?")
        self.assertNotContains(interests_page, "How far along are you in that course?")

        empty_interests = self.client.post(reverse("onboarding") + "?step=4", {
            "step": "4",
            "action": "next",
        })
        self.assertEqual(empty_interests.status_code, 200)
        self.assertContains(empty_interests, "Please pick at least one interest")

        interests = self.client.post(reverse("onboarding") + "?step=4", {
            "step": "4",
            "action": "next",
            "interest": ["Python", "Machine Learning"],
        })
        self.assertRedirects(interests, reverse("onboarding") + "?step=5")

        goal_page = self.client.get(reverse("onboarding") + "?step=5")
        self.assertContains(goal_page, "What would you like help with first?")
        self.assertContains(goal_page, "5 of 5")
        self.assertNotContains(goal_page, "Which skills would you like us to match for you?")

        goal = self.client.post(reverse("onboarding") + "?step=5", {
            "step": "5",
            "action": "next",
            "learning_goal": "Explore AI, data, and machine learning",
        })
        self.assertRedirects(goal, reverse("onboarding") + "?step=6")

        ready = self.client.get(reverse("onboarding") + "?step=6")
        self.assertContains(ready, "Thank you, Amina Patel.")
        self.assertContains(ready, "Open my dashboard")
        self.assertNotContains(ready, "May we start with the name you like to be called?")

        opened = self.client.post(reverse("onboarding"), {
            "step": "6",
            "action": "open_app",
        })
        self.assertRedirects(opened, reverse("dashboard"))

        profile = StudentProfile.objects.get(user=user)
        self.assertEqual(profile.full_name, "Amina Patel")
        self.assertEqual(profile.course, "B.Tech Computer Science")
        self.assertEqual(profile.year_of_study, 2)
        self.assertIn("Python", profile.interests)
        self.assertIn("Machine Learning", profile.interests)
        self.assertEqual(profile.learning_goal, "Explore AI, data, and machine learning")
        self.assertTrue(profile.onboarding_complete)
        self.assertFalse(profile.needs_onboarding())

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Amina Patel")
        self.assertContains(dashboard, "B.Tech Computer Science")
        recommended_names = [
            rec.skill_name for rec in dashboard.context["recommendations"]["recommended_skills"]
        ]
        self.assertTrue(recommended_names)
        self.assertIn(recommended_names[0], {"Python Programming", "Machine Learning"})

