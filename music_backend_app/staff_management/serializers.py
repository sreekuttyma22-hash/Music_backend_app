from rest_framework import serializers

from .models import Staff


# =========================================================
# STAFF SERIALIZER
# =========================================================

class StaffSerializer(serializers.ModelSerializer):

    class Meta:

        model = Staff

        fields = [
            'id',
            'staff_number',
            'user',
            'first_name',
            'last_name',
            'email',
            'phone',
            'profile_image',
            'date_of_birth',
            'gender',
            'address',
            'qualification',
            'emergency_contact_name',
            'emergency_contact_phone',
            'location',
            'admin_enabled',
            'is_admin',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'staff_number',
            'user',
            'created_at',
            'updated_at',
            'location',
        ]


# =========================================================
# STAFF CREATE SERIALIZER
# =========================================================

class StaffCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:

        model = Staff

        fields = [
            'id',
            'staff_number',
            'user',
            'first_name',
            'last_name',
            'email',
            'phone',
            'profile_image',
            'date_of_birth',
            'gender',
            'address',
            'qualification',
            'emergency_contact_name',
            'emergency_contact_phone',
            'password',
            'admin_enabled',
            'is_admin',
            'is_active',
        ]

        read_only_fields = [
            'id',
            'staff_number',
            'user',
            'location',
        ]

    def create(self, validated_data):

        password = validated_data.pop(
            'password'
        )

        staff = Staff(
            **validated_data
        )

        staff.set_password(password)

        staff.save()

        return staff


# =========================================================
# STAFF UPDATE SERIALIZER
# =========================================================

class StaffUpdateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=6
    )

    class Meta:

        model = Staff

        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'profile_image',
            'date_of_birth',
            'gender',
            'address',
            'qualification',
            'emergency_contact_name',
            'emergency_contact_phone',
            'password',
            'admin_enabled',
            'is_active',
        ]

    def update(self, instance, validated_data):

        password = validated_data.pop(
            'password',
            None
        )

        for attr, value in validated_data.items():
            setattr(
                instance,
                attr,
                value
            )

        if password:
            instance.set_password(
                password
            )

        instance.save()

        return instance
