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
        LearningResource.objects.create(
            skill=machine_learning,
            title="Inactive Course",
            url="https://example.com/inactive",
            is_active=False,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["learning_resources"]), 2)
        self.assertContains(response, "Python Course")
        self.assertContains(response, "Machine Learning Course")
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
            "course": "BCA Data Science",
            "year_of_study": 2,
            "interests": "Python, SQL, Tableau",
        }
        form = StudentProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_profile_edit_view_post_updates_database(self):
        client = Client()
        client.login(username="john_doe", password="SecurePassword123!")

        post_data = {
            "full_name": "John Doe Updated",
            "course": "M.Sc AI & Robotics",
            "year_of_study": 4,
            "interests": "Robotics, ROS, Python",
        }
        response = client.post(reverse("edit_profile"), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        profile = StudentProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "John Doe Updated")
        self.assertEqual(profile.course, "M.Sc AI & Robotics")
        self.assertEqual(profile.year_of_study, 4)
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
