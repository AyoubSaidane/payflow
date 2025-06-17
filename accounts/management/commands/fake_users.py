from django.core.management import BaseCommand
from faker import Faker

from accounts.models import User


class Command(BaseCommand):
    help = "Tâche automatisée de création de faux utilisateurs pour tester l'application"

    def handle(self, *args, **options):
        fake = Faker('fr_FR')
        User.objects.filter(is_superuser=False).delete()
        users = []
        for i in range(30):
            entire_name = fake.name().split(' ')
            users.append(User(
                first_name=entire_name[0],
                last_name=" ".join(entire_name[1:]),
                username=entire_name[0][:3]+entire_name[1][:3]+str(i),
                email=f"{entire_name[0]}.{entire_name[1]}@gmail.com",
                telephone=fake.phone_number(),
                password="password"
            ))

        User.objects.bulk_create(users)
