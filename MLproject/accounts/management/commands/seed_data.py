from django.core.management.base import BaseCommand
from accounts.models import Skill, LearningResource


class Command(BaseCommand):
    help = "Seeds initial skills, learning materials, and course links into the database."

    def handle(self, *args, **options):
        self.stdout.write("Seeding skills and learning resources...")

        skills_data = [
            {
                "name": "Python Programming",
                "category": "Programming Languages",
                "keywords": "python, py, scripting, backend, oop, data structures, automation",
                "description": "Foundational high-level programming language essential for AI, data science, and backend development.",
                "resources": [
                    {
                        "title": "CS50's Introduction to Programming with Python",
                        "platform": "Harvard / edX",
                        "resource_type": "course",
                        "difficulty": "beginner",
                        "url": "https://cs50.harvard.edu/python/",
                        "description": "An introduction to programming using Python, covering functions, variables, conditionals, loops, and libraries.",
                    },
                    {
                        "title": "Python Official Tutorial & Documentation",
                        "platform": "Python Software Foundation",
                        "resource_type": "documentation",
                        "difficulty": "beginner",
                        "url": "https://docs.python.org/3/tutorial/",
                        "description": "Official comprehensive guide to the Python programming language.",
                    },
                    {
                        "title": "Real Python Learning Paths & Best Practices",
                        "platform": "Real Python",
                        "resource_type": "tutorial",
                        "difficulty": "intermediate",
                        "url": "https://realpython.com/",
                        "description": "In-depth tutorials covering idiomatic Python, decorators, OOP, and async programming.",
                    },
                ],
            },
            {
                "name": "Machine Learning",
                "category": "Artificial Intelligence",
                "keywords": "ml, machine learning, supervised learning, unsupervised, regression, classification, scikit-learn",
                "description": "Core algorithms for pattern recognition and predictive modeling from data.",
                "resources": [
                    {
                        "title": "Machine Learning Specialization by Andrew Ng",
                        "platform": "Coursera / DeepLearning.AI",
                        "resource_type": "course",
                        "difficulty": "beginner",
                        "url": "https://www.coursera.org/specializations/machine-learning-introduction",
                        "description": "Foundational online program teaching modern machine learning concepts from the ground up.",
                    },
                    {
                        "title": "Scikit-Learn User Guide & API Reference",
                        "platform": "Scikit-Learn Docs",
                        "resource_type": "documentation",
                        "difficulty": "intermediate",
                        "url": "https://scikit-learn.org/stable/user_guide.html",
                        "description": "Complete documentation for standard machine learning algorithms in Python.",
                    },
                    {
                        "title": "Kaggle Machine Learning Micro-Courses",
                        "platform": "Kaggle",
                        "resource_type": "project",
                        "difficulty": "beginner",
                        "url": "https://www.kaggle.com/learn",
                        "description": "Hands-on coding exercises with real datasets and competitions.",
                    },
                ],
            },
            {
                "name": "Deep Learning & Neural Networks",
                "category": "Artificial Intelligence",
                "keywords": "deep learning, dl, neural networks, pytorch, tensorflow, backpropagation, cnn, rnn",
                "description": "Hierarchical representation learning and deep artificial neural networks for complex data.",
                "resources": [
                    {
                        "title": "Deep Learning Specialization",
                        "platform": "Coursera / DeepLearning.AI",
                        "resource_type": "course",
                        "difficulty": "intermediate",
                        "url": "https://www.coursera.org/specializations/deep-learning",
                        "description": "Master deep learning, construct neural networks, and lead successful ML projects.",
                    },
                    {
                        "title": "PyTorch 60-Minute Blitz & Tutorials",
                        "platform": "PyTorch.org",
                        "resource_type": "tutorial",
                        "difficulty": "intermediate",
                        "url": "https://pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html",
                        "description": "Fast-paced introduction to tensors, autograd, and training neural networks in PyTorch.",
                    },
                    {
                        "title": "Practical Deep Learning for Coders",
                        "platform": "Fast.ai",
                        "resource_type": "course",
                        "difficulty": "intermediate",
                        "url": "https://course.fast.ai/",
                        "description": "A top-down, hands-on deep learning course for software developers.",
                    },
                ],
            },
            {
                "name": "Data Science & Analysis",
                "category": "Data Science",
                "keywords": "data science, ds, data analysis, pandas, numpy, matplotlib, seaborn, exploratory data analysis, eda, statistics",
                "description": "Extracting actionable insights, cleaning tabular data, and creating effective visualizations.",
                "resources": [
                    {
                        "title": "Python for Data Analysis (Wes McKinney)",
                        "platform": "Open Reference",
                        "resource_type": "book",
                        "difficulty": "beginner",
                        "url": "https://wesmckinney.com/book/",
                        "description": "Authoritative guide to data wrangling and numerical analysis with Pandas and NumPy.",
                    },
                    {
                        "title": "Google Data Analytics Professional Certificate",
                        "platform": "Coursera / Google",
                        "resource_type": "course",
                        "difficulty": "beginner",
                        "url": "https://www.coursera.org/professional-certificates/google-data-analytics",
                        "description": "Comprehensive program covering data cleaning, analysis, and visualization.",
                    },
                ],
            },
            {
                "name": "Web Development & Django",
                "category": "Web Development",
                "keywords": "web development, web, fullstack, backend, frontend, django, html, css, rest api, javascript",
                "description": "Building full-stack scalable web applications, REST APIs, and database-driven websites.",
                "resources": [
                    {
                        "title": "Official Django Documentation & Tutorial",
                        "platform": "Django Project",
                        "resource_type": "documentation",
                        "difficulty": "beginner",
                        "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
                        "description": "Step-by-step tutorial building a web application using the Django framework.",
                    },
                    {
                        "title": "MDN Web Docs: Web Development Curriculum",
                        "platform": "Mozilla Developer Network",
                        "resource_type": "tutorial",
                        "difficulty": "beginner",
                        "url": "https://developer.mozilla.org/en-US/docs/Learn",
                        "description": "Complete beginner to intermediate web standards reference covering HTML, CSS, and JS.",
                    },
                    {
                        "title": "Full Stack Open",
                        "platform": "University of Helsinki",
                        "resource_type": "course",
                        "difficulty": "intermediate",
                        "url": "https://fullstackopen.com/en/",
                        "description": "Modern full-stack web development with React, Node.js, and REST APIs.",
                    },
                ],
            },
            {
                "name": "Natural Language Processing (NLP)",
                "category": "Artificial Intelligence",
                "keywords": "nlp, natural language processing, transformers, bert, gpt, llm, text processing, tokenization",
                "description": "Techniques for computer understanding, translation, and generation of human languages.",
                "resources": [
                    {
                        "title": "Hugging Face NLP Course",
                        "platform": "Hugging Face",
                        "resource_type": "course",
                        "difficulty": "intermediate",
                        "url": "https://huggingface.co/learn/nlp-course/",
                        "description": "Learn to use Transformers and the Hugging Face ecosystem for state-of-the-art NLP models.",
                    },
                    {
                        "title": "Stanford CS224N: Natural Language Processing with Deep Learning",
                        "platform": "Stanford Online / YouTube",
                        "resource_type": "video",
                        "difficulty": "advanced",
                        "url": "https://web.stanford.edu/class/cs224n/",
                        "description": "World-class university lectures covering deep learning for natural language.",
                    },
                ],
            },
        ]

        total_skills_created = 0
        total_resources_created = 0

        for s_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=s_data["name"],
                defaults={
                    "category": s_data["category"],
                    "keywords": s_data["keywords"],
                    "description": s_data["description"],
                },
            )
            if created:
                total_skills_created += 1

            for r_data in s_data["resources"]:
                resource, res_created = LearningResource.objects.get_or_create(
                    skill=skill,
                    title=r_data["title"],
                    defaults={
                        "platform": r_data["platform"],
                        "resource_type": r_data["resource_type"],
                        "difficulty": r_data["difficulty"],
                        "url": r_data["url"],
                        "description": r_data["description"],
                        "is_active": True,
                    },
                )
                if res_created:
                    total_resources_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded database! ({total_skills_created} new skills, {total_resources_created} new resources)"
            )
        )

