from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Staff


class StaffJWTAuthentication(
    JWTAuthentication
):

    def get_user(self, validated_token):

        # Get staff ID from JWT
        try:

            staff_id = validated_token[
                'staff_id'
            ]

        except KeyError:

            raise AuthenticationFailed(
                'Invalid token.'
            )

        # Find staff
        try:

            staff = Staff.objects.get(
                id=staff_id
            )

        except Staff.DoesNotExist:

            raise AuthenticationFailed(
                'Staff not found.'
            )

        # Check active status
        if not staff.is_active:

            raise AuthenticationFailed(
                'Staff account is inactive.'
            )

        if not staff.admin_enabled:
            raise AuthenticationFailed(
                'Staff account is awaiting administrator approval.'
            )

        return staff