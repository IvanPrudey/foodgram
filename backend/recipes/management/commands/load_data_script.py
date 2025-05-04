import csv
from pathlib import Path
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import data from a CSV files'

    def handle(self, *args, **kwargs):
        self.load_ingredients()
        self.stdout.write(
            self.style.SUCCESS('Loading of ingredients is completed')
        )

    def load_ingredients(self):
        csv_path = (
            Path(__file__).resolve().parents[3]
            / 'data'
            / 'ingredients.csv'
        )
        if not csv_path.exists():
            self.stdout.write(
                self.style.ERROR(f'File {csv_path} not found!')
            )
            return

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Ingredient.objects.update_or_create(
                    name=row['name'],
                    measurement_unit=row['measurement_unit']
                )
