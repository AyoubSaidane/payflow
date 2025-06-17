from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from django.contrib.auth.models import Group
from django.conf import settings


class UserTestCase(TestCase):

    def setUp(self):
        call_command("init_groups")
        self.admin_group = Group.objects.get(name=settings.GROUP_ADMIN_USER)
        self.admin_user = User.objects.create(email="admin_user@safeflat.fr", username="admin_user", first_name="John",last_name="Doe")
        self.admin_user.set_password('123456TEST')
        self.admin_user.groups.add(self.admin_group)
        self.admin_user.save()

        self.standard_group = Group.objects.get(name=settings.GROUP_STANDARD_USER)
        self.standard_user = User.objects.create(email="standard_user@safeflat.fr", username="standard_user", first_name="Jane", last_name="Doe")
        self.standard_user.set_password('123456TEST')
        self.standard_user.groups.add(self.standard_group)
        self.standard_user.save()

    def test_UserList(self):
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        response = self.client.get(reverse('accounts:user-list'),{"query":"doe john"})
        self.assertEqual(response.context["object_list"].count(), 1)
        response = self.client.get(reverse('accounts:user-list'), {"group": self.admin_group.pk})
        self.assertEqual(response.context["object_list"].count(), 1)

    def test_UserCreate(self):
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-create')
        self.client.post(url, data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@safeflat.fr",
            "group": self.admin_group.pk
        })
        self.client.login(username='john.doe@safeflat.fr', password='54321TEST')
        response = self.client.get(reverse('accounts:user-list'))
        self.assertEqual(response.status_code, 200)
        john = User.objects.get(email='john.doe@safeflat.fr')
        self.assertEqual(john.groups.first(), self.admin_group)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox[0].subject, 'Your account credentials')
        self.assertListEqual(mail.outbox[0].recipients(), ['john.doe@safeflat.fr'])

    def test_UserUpdate(self):
        """
        Test that admin can update a user
        """
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-update',args=(self.admin_user.uuid,))
        standard = Group.objects.get(name=settings.GROUP_STANDARD_USER)
        response = self.client.post(url, data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@safeflat.fr",
            "password": "54321TEST",
            "group": standard.pk
        })
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.groups.first(),standard)

    def test_UserDelete(self):
        """
        Test that admin can delete a user
        """
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-delete', args=(self.standard_user.uuid,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url,{"action": "delete"})
        self.assertEqual(User.objects.filter(uuid=self.standard_user.uuid).count(), 0)

    def test_UserDisable(self):
        """
        Test that admin can disable a user
        """
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-delete', args=(self.standard_user.uuid,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url,{"action": "disable"})
        self.standard_user.refresh_from_db()
        self.assertFalse(self.standard_user.is_active)


    def test_GeneratePassword(self):
        """
        Test that admin can generate a new password for a user
        """
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-newpassword',args=(self.admin_user.uuid, ))
        self.client.post(url)
        self.assertEqual(mail.outbox[0].subject, 'Your account credentials')
        self.assertListEqual(mail.outbox[0].recipients(), ['admin_user@safeflat.fr'])

    def test_UserUpdatePasswordSelf(self):
        """
        Test that user can update its password
        """
        self.client.login(username='admin_user@safeflat.fr', password='123456TEST')
        url = reverse('accounts:user-update-password-self')
        self.client.post(url,{'password1':'totolafrite','password2':'password2'})
        self.assertTrue(url,self.admin_user.check_password('totolafrite'))
