import json
import os
from django.core.management.base import BaseCommand
from extras.models import Achievement


class Command(BaseCommand):
    help = 'Load achievements from JSON file'

    def handle(self, *args, **kwargs):
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, '..', '..', 'fixtures', 'achievements.json')
        file_path = os.path.normpath(file_path)

        self.stdout.write(f"Loading achievements from: {file_path}")

        with open(file_path, 'r') as f:
            data = json.load(f)

        for item in data:
            fields = item['fields']  # <-- access the nested fields dict
            Achievement.objects.update_or_create(
                title=fields['title'],
                defaults={
                    'description': fields['description'],
                    'icon': fields['icon'],
                    'required_level': fields['required_level']
                }
            )

        self.stdout.write(self.style.SUCCESS('Achievements loaded successfully.'))
