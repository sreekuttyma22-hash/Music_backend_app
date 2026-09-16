from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Staff(models.Model):

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    staff_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    profile_image = models.ImageField(
        upload_to='staff/',
        null=True,
        blank=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    qualification = models.CharField(
        max_length=255,
        blank=True,
    )

    emergency_contact_name = models.CharField(
        max_length=255,
        blank=True,
    )

    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    location = models.ForeignKey(
        'students_management.Location',
        on_delete=models.CASCADE,
        related_name='staff_members',
        null=True,
        blank=True,
    )

    password = models.CharField(
        max_length=255
    )

    # Staff can login only when this is True
    admin_enabled = models.BooleanField(
        default=False
    )

    # Only administrator accounts can approve or manage staff accounts.
    is_admin = models.BooleanField(
        default=False
    )

    # Account active/inactive status
    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if not self.staff_number:

            last_staff = Staff.objects.order_by('-id').first()

            if last_staff:
                next_id = last_staff.id + 1
            else:
                next_id = 1

            self.staff_number = f"STF-{next_id:05d}"

        super().save(*args, **kwargs)
        self._sync_user()

    def _sync_user(self):
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        user = self.user

        if user is None:
            user = user_model.objects.create(username=self.email[:150])
            self.user = user
            type(self).objects.filter(pk=self.pk).update(user=user)

        user.first_name = self.first_name
        user.last_name = self.last_name
        user.email = self.email
        user.is_active = self.is_active and self.admin_enabled
        user.is_staff = self.admin_enabled and self.is_active
        user.is_superuser = (
            self.is_admin
            and self.admin_enabled
            and self.is_active
        )
        if self.password:
            user.password = self.password
        else:
            user.set_unusable_password()
        user.save(update_fields=[
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
            'password',
        ])

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(
            raw_password,
            self.password
        )

    @property
    def is_authenticated(self):
        """
        Always return True for Staff instances.
        Since Staff objects are only set as request.user
        after successful authentication, they are by definition authenticated.
        """
        return True

    def __str__(self):
        return (
            f"{self.staff_number} - "
            f"{self.first_name} {self.last_name}"
        )
