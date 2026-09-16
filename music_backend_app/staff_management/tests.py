from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Staff


class StaffApprovalTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.staff = Staff.objects.create(
			first_name="Pending",
			last_name="Staff",
			email="pending@example.com",
		)
		self.staff.set_password("password123")
		self.staff.save(update_fields=["password"])

		self.admin = Staff.objects.create(
			first_name="Main",
			last_name="Admin",
			email="admin@example.com",
			admin_enabled=True,
			is_admin=True,
		)
		self.admin.set_password("password123")
		self.admin.save(update_fields=["password"])

	def test_unapproved_staff_cannot_login(self):
		response = self.client.post(
			"/api/staff/login/",
			{"email": self.staff.email, "password": "password123"},
			format="json",
		)

		self.assertEqual(response.status_code, 403)
		self.assertIn("awaiting administrator approval", response.data["message"])

	def test_approved_staff_can_login(self):
		self.staff.admin_enabled = True
		self.staff.save(update_fields=["admin_enabled"])

		response = self.client.post(
			"/api/staff/login/",
			{"email": self.staff.email, "password": "password123"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("access", response.data)

	def test_staff_is_synced_to_django_user(self):
		self.staff.admin_enabled = True
		self.staff.save(update_fields=["admin_enabled"])

		user = User.objects.get(pk=self.staff.user_id)
		self.assertEqual(user.email, self.staff.email)
		self.assertTrue(user.is_active)
		self.assertTrue(user.is_staff)
		self.assertFalse(user.is_superuser)
		self.assertTrue(user.check_password("password123"))

	def test_approved_active_admin_is_django_superuser(self):
		user = User.objects.get(pk=self.admin.user_id)
		self.assertTrue(user.is_active)
		self.assertTrue(user.is_staff)
		self.assertTrue(user.is_superuser)
		self.assertTrue(user.check_password("password123"))

	def test_only_admin_can_approve_staff(self):
		response = self.client.patch(
			f"/api/staff/{self.staff.id}/approval/",
			{"admin_enabled": True},
			format="json",
		)
		self.assertEqual(response.status_code, 401)

		token = RefreshToken()
		token["staff_id"] = self.admin.id
		token["email"] = self.admin.email
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

		response = self.client.patch(
			f"/api/staff/{self.staff.id}/approval/",
			{"admin_enabled": True},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.staff.refresh_from_db()
		self.assertTrue(self.staff.admin_enabled)

	def test_registration_accepts_staff_profile_fields(self):
		response = self.client.post(
			"/api/staff/create/",
			{
				"first_name": "Profile",
				"last_name": "Staff",
				"email": "profile@example.com",
				"phone": "123456789",
				"password": "password123",
				"date_of_birth": "1995-04-20",
				"gender": "female",
				"address": "Main Street",
				"qualification": "Music Diploma",
				"emergency_contact_name": "Emergency Contact",
				"emergency_contact_phone": "987654321",
				"admin_enabled": True,
				"is_admin": True,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		registered = Staff.objects.get(email="profile@example.com")
		self.assertEqual(registered.qualification, "Music Diploma")
		self.assertEqual(registered.address, "Main Street")
		self.assertFalse(registered.admin_enabled)
		self.assertFalse(registered.is_admin)

	def test_admin_can_get_and_update_staff_detail(self):
		token = RefreshToken()
		token["staff_id"] = self.admin.id
		token["email"] = self.admin.email
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

		response = self.client.get(f"/api/staff/{self.staff.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["result"]["id"], self.staff.id)

		response = self.client.patch(
			f"/api/staff/{self.staff.id}/",
			{"qualification": "Updated Diploma", "address": "New Address"},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.staff.refresh_from_db()
		self.assertEqual(self.staff.qualification, "Updated Diploma")
		self.assertEqual(self.staff.address, "New Address")
