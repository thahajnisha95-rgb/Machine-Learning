from django.core.management.base import BaseCommand
from student_learning_system import train_recommender_system


class Command(BaseCommand):
    help = "Trains the TF-IDF Vectorizer and Cosine Similarity recommender weights on all skills and resources."

    def handle(self, *args, **options):
        self.stdout.write("Training TF-IDF Recommender Engine from database...")
        stats = train_recommender_system()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully trained ML recommender!\n"
                f"- Documents indexed: {stats['doc_count']}\n"
                f"- Vocabulary size: {stats['vocabulary_size']} terms\n"
                f"- Skill vectors created: {stats['skills_indexed']}"
            )
        )

