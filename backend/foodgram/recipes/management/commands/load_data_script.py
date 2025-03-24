import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


PATH_CSV_FILES = './data/'


class Command(BaseCommand):
    help = 'Import data from a CSV files'

    def handle(self, *args, **kwargs):
        self.load_ingredients()
        print('Loading of ingredients is completed')

    def load_ingredients(self):
        Ingredient.objects.all().delete()
        with open(
            f'{PATH_CSV_FILES}ingredients.csv', 'r', encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'measurement_unit': row['measurement_unit']
                    }
                )
