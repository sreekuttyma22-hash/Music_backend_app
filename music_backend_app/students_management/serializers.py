# # students/serializers.py

import json
import re
from decimal import Decimal

from rest_framework import serializers
from django.db import transaction
from .models import Location, Room, Student, Instructor, Category
# import json



class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id", "name", "code", "address", "phone", "email", "active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "location", "name", "capacity", "active"]
        read_only_fields = ["id", "location"]


class StudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = "__all__"
        read_only_fields = [
            "id",
            "student_number",
            "active",
            "payment_status",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value):
        if value:
            return value.lower()
        return value


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]



class InstructorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Instructor
        fields = "__all__"
        read_only_fields = [
            "id",
            "instructor_number",
            "created_at",
            "updated_at",
            "location",
            "location",
        ]




from .models import (
    Student,
    Instructor,
    Appointment,
    Course,
    LessonType,
    LessonDuration,
    LessonMode,
    CoursePricing,
    CoursePackage,
    CoursePackagePrice,
    Enrollment,
)

class CourseSerializer(serializers.ModelSerializer):
    """
    Course API used by CoursesPage.jsx.

    The frontend sends one combination_pricing array containing:
        level x mode x lesson_duration x package

    The database stores those values in the normalized:
        CoursePricing
        CoursePackage
        CoursePackagePrice
    tables.
    """

    instructor_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Instructor.objects.all(),
        source="instructors",
        write_only=True,
        required=False,
    )

    # Also accept the field name currently sent by CoursesPage.jsx.
    # It is converted to instructor_ids in to_internal_value().
    instructors = serializers.SerializerMethodField(read_only=True)

    pricing = serializers.SerializerMethodField(read_only=True)
    packages = serializers.SerializerMethodField(read_only=True)
    enrolled_students = serializers.SerializerMethodField(read_only=True)

    combination_pricing = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "course_number",
            "course_name",
            "category",
            "description",
            "level",
            "selected_levels",
            "selected_modes",
            "selected_lesson_durations",
            "selected_packages",
            "instructor_ids",
            "instructors",
            "pricing",
            "packages",
            "combination_pricing",
            "enrolled_students",
            "status",
            "image",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "course_number",
            "instructors",
            "pricing",
            "packages",
            "enrolled_students",
            "created_at",
            "updated_at",
        ]

    def to_internal_value(self, data):
        """Accept JSON and multipart/form-data from the React page."""
        # QueryDict.copy() performs a deepcopy.  That fails for uploaded files,
        # so build a shallow mapping when handling multipart form data.
        if hasattr(data, "lists"):
            data = {
                key: values if len(values) > 1 else values[0]
                for key, values in data.lists()
            }
        else:
            data = data.copy()

        # Multipart form fields may arrive as JSON strings.
        json_fields = [
            "selected_levels",
            "selected_modes",
            "selected_lesson_durations",
            "selected_packages",
            "combination_pricing",
        ]

        for field in json_fields:
            value = data.get(field)
            if isinstance(value, str):
                try:
                    data[field] = json.loads(value)
                except (TypeError, ValueError, json.JSONDecodeError):
                    pass

        # CoursesPage.jsx currently sends instructors: [1, 2, ...].
        # The serializer's write field is instructor_ids.
        if "instructors" in data and "instructor_ids" not in data:
            value = data.get("instructors")

            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except (TypeError, ValueError, json.JSONDecodeError):
                    value = [value]

            if isinstance(value, list):
                ids = []
                for item in value:
                    if isinstance(item, dict):
                        if item.get("id") is not None:
                            ids.append(item["id"])
                    elif item not in (None, ""):
                        ids.append(item)
                data["instructor_ids"] = ids

            data.pop("instructors", None)

        return super().to_internal_value(data)

    def validate(self, attrs):
        selected_levels = attrs.get("selected_levels")
        if selected_levels:
            valid_levels = {choice[0] for choice in Course.LEVEL_CHOICES}
            invalid = [x for x in selected_levels if x not in valid_levels]
            if invalid:
                raise serializers.ValidationError({
                    "selected_levels": f"Invalid level(s): {invalid}"
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        combination_pricing = validated_data.pop("combination_pricing", [])
        instructors = validated_data.pop("instructors", [])

        selected_levels = validated_data.get("selected_levels") or []
        if selected_levels:
            validated_data["level"] = selected_levels[0]

        course = Course.objects.create(**validated_data)

        if instructors:
            course.instructors.set(instructors)

        self._save_combination_pricing(course, combination_pricing)
        return course

    @transaction.atomic
    def update(self, instance, validated_data):
        combination_pricing = validated_data.pop("combination_pricing", None)
        instructors = validated_data.pop("instructors", None)

        selected_levels = validated_data.get("selected_levels")
        if selected_levels:
            validated_data["level"] = selected_levels[0]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instructors is not None:
            instance.instructors.set(instructors)

        if combination_pricing is not None:
            self._save_combination_pricing(instance, combination_pricing)

        return instance

    def _save_combination_pricing(self, course, combinations):
        """Convert CoursesPage pricing matrix into normalized DB rows."""
        if not combinations:
            # An explicitly empty matrix means the course currently has
            # no active pricing. Do not create anything.
            CoursePricing.objects.filter(course=course).update(active=False)
            CoursePackage.objects.filter(course=course).update(active=False)
            CoursePackagePrice.objects.filter(package__course=course).update(active=False)
            return

        lesson_type, _ = LessonType.objects.get_or_create(
            code="private",
            defaults={"name": "Private", "active": True},
        )
        if not lesson_type.active:
            lesson_type.active = True
            lesson_type.save(update_fields=["active"])

        mode_map = {
            "online": "online",
            "offline": "institute",
            "institute": "institute",
            "home_visit": "home_visit",
        }

        mode_names = {
            "online": "Online",
            "institute": "Institute",
            "home_visit": "Home Visit",
        }

        duration_map = {
            "30_min": 30,
            "45_min": 45,
            "60_min": 60,
            "90_min": 90,
        }

        used_pricing_ids = set()
        used_package_ids = set()

        for combination in combinations:
            level = combination.get("level")
            frontend_mode = combination.get("mode")
            duration_key = combination.get("lesson_duration")
            package_key = combination.get("package")

            if not all([level, frontend_mode, duration_key, package_key]):
                raise serializers.ValidationError({
                    "combination_pricing": (
                        "Each pricing combination must contain "
                        "level, mode, lesson_duration and package."
                    )
                })

            valid_levels = {choice[0] for choice in Course.LEVEL_CHOICES}
            if level not in valid_levels:
                raise serializers.ValidationError({
                    "combination_pricing": f"Invalid level: {level}"
                })

            backend_mode = mode_map.get(frontend_mode)
            if not backend_mode:
                raise serializers.ValidationError({
                    "combination_pricing": f"Invalid mode: {frontend_mode}"
                })

            mode, _ = LessonMode.objects.get_or_create(
                code=backend_mode,
                defaults={
                    "name": mode_names[backend_mode],
                    "additional_fee": Decimal("0"),
                    "active": True,
                },
            )
            if not mode.active:
                mode.active = True
                mode.save(update_fields=["active"])

            minutes = duration_map.get(duration_key)
            if minutes is None and isinstance(duration_key, str) and duration_key.endswith("_min"):
                try:
                    minutes = int(duration_key[:-4])
                except ValueError:
                    minutes = None

            if minutes is None or minutes <= 0:
                raise serializers.ValidationError({
                    "combination_pricing": f"Invalid lesson duration: {duration_key}"
                })

            duration, _ = LessonDuration.objects.get_or_create(
                minutes=minutes,
                defaults={"active": True},
            )
            if not duration.active:
                duration.active = True
                duration.save(update_fields=["active"])

            per_lesson_value = combination.get("per_lesson_price")
            if per_lesson_value in (None, ""):
                per_lesson_value = combination.get("price", 0)

            try:
                per_lesson_price = Decimal(str(per_lesson_value))
            except Exception:
                raise serializers.ValidationError({
                    "combination_pricing": (
                        f"Invalid per_lesson_price: {per_lesson_value}"
                    )
                })

            if per_lesson_price < 0:
                raise serializers.ValidationError({
                    "combination_pricing": "Price cannot be negative."
                })

            currency = combination.get("currency", "₹")
            if currency in ("₹", "INR", "inr"):
                currency = "INR"

            pricing, _ = CoursePricing.objects.update_or_create(
                course=course,
                lesson_type=lesson_type,
                duration=duration,
                mode=mode,
                level=level,
                defaults={
                    "price": per_lesson_price,
                    "currency": currency,
                    "active": True,
                },
            )
            used_pricing_ids.add(pricing.id)

            package_defaults = self._package_defaults(package_key)
            package, _ = CoursePackage.objects.update_or_create(
                course=course,
                name=package_defaults["name"],
                defaults={
                    "lesson_count": package_defaults["lesson_count"],
                    "discount_percentage": package_defaults["discount"],
                    "active": True,
                },
            )
            used_package_ids.add(package.id)

            final_value = combination.get("price")
            if final_value in (None, ""):
                final_value = per_lesson_price * package.lesson_count

            try:
                final_price = Decimal(str(final_value))
            except Exception:
                raise serializers.ValidationError({
                    "combination_pricing": f"Invalid package price: {final_value}"
                })

            if final_price < 0:
                raise serializers.ValidationError({
                    "combination_pricing": "Package price cannot be negative."
                })

            CoursePackagePrice.objects.update_or_create(
                package=package,
                pricing=pricing,
                defaults={
                    "price": final_price,
                    "currency": currency,
                    "active": True,
                },
            )

        # Anything not represented by the current matrix is no longer active.
        if used_pricing_ids:
            CoursePricing.objects.filter(course=course).exclude(
                id__in=used_pricing_ids
            ).update(active=False)

        if used_package_ids:
            CoursePackage.objects.filter(course=course).exclude(
                id__in=used_package_ids
            ).update(active=False)

        CoursePackagePrice.objects.filter(
            package__course=course
        ).filter(
            package__active=False
        ).update(active=False)

        CoursePackagePrice.objects.filter(
            pricing__course=course
        ).exclude(
            pricing_id__in=used_pricing_ids
        ).update(active=False)

    @staticmethod
    def _package_defaults(package_key):
        """Convert a frontend key such as ``10_lessons`` into a package."""
        match = re.fullmatch(r"([1-9]\d*)_lessons", str(package_key))
        if not match:
            raise serializers.ValidationError({
                "combination_pricing": (
                    "Invalid package. Use a positive lesson-count key, "
                    "for example '2_lessons' or '10_lessons'."
                )
            })

        lesson_count = int(match.group(1))
        return {
            "name": f"{lesson_count} Lesson{'s' if lesson_count != 1 else ''}",
            "lesson_count": lesson_count,
            "discount": 0,
        }

    def get_instructors(self, obj):
        return [
            {
                "id": instructor.id,
                "instructor_name": instructor.instructor_name,
                "instructor_number": instructor.instructor_number,
                "profile_image": (
                    instructor.profile_image.url
                    if instructor.profile_image
                    else None
                ),
                "specialization": instructor.specialization,
                "experience_years": instructor.experience_years,
                "email": instructor.email,
                "phone": instructor.phone,
            }
            for instructor in obj.instructors.all()
        ]

    def get_pricing(self, obj):
        return [
            {
                "id": item.id,
                "lesson_type": {
                    "id": item.lesson_type.id,
                    "name": item.lesson_type.name,
                    "code": item.lesson_type.code,
                },
                "duration": {
                    "id": item.duration.id,
                    "minutes": item.duration.minutes,
                },
                "mode": {
                    "id": item.mode.id,
                    "name": item.mode.name,
                    "code": item.mode.code,
                    "additional_fee": str(item.mode.additional_fee),
                },
                "level": item.level,
                "price": str(item.price),
                "currency": "₹" if item.currency == "INR" else item.currency,
                "active": item.active,
            }
            for item in obj.pricing.select_related(
                "lesson_type",
                "duration",
                "mode",
            ).filter(active=True)
        ]

    def get_packages(self, obj):
        packages = []

        for package in obj.packages.filter(active=True):
            package_prices = []

            for package_price in package.prices.select_related(
                "pricing",
                "pricing__duration",
                "pricing__mode",
            ).filter(active=True):
                pricing = package_price.pricing
                package_prices.append({
                    "pricing_id": pricing.id,
                    "price": str(package_price.price),
                    "currency": (
                        "₹" if package_price.currency == "INR"
                        else package_price.currency
                    ),
                    "level": pricing.level,
                    "mode": (
                        "offline" if pricing.mode.code == "institute"
                        else pricing.mode.code
                    ),
                    "lesson_duration": f"{pricing.duration.minutes}_min",
                })

            packages.append({
                "id": package.id,
                "name": package.name,
                "lesson_count": package.lesson_count,
                "discount_percentage": str(package.discount_percentage),
                "active": package.active,
                "prices": package_prices,
            })

        return packages

    def get_enrolled_students(self, obj):
        return obj.enrollments.filter(
            status="active"
        ).values("student").distinct().count()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        combinations = []

        for package in instance.packages.filter(active=True):
            for package_price in package.prices.select_related(
                "pricing",
                "pricing__duration",
                "pricing__mode",
            ).filter(active=True):
                pricing = package_price.pricing
                base_price = pricing.price * package.lesson_count

                combinations.append({
                    "level": pricing.level,
                    "mode": (
                        "offline" if pricing.mode.code == "institute"
                        else pricing.mode.code
                    ),
                    "lesson_duration": f"{pricing.duration.minutes}_min",
                    "package": self._package_key(package),
                    "per_lesson_price": float(pricing.price),
                    "price": float(package_price.price),
                    "base_price": float(base_price),
                    "discount": float(base_price - package_price.price),
                    "currency": "₹" if package_price.currency == "INR" else package_price.currency,
                })

        data["combination_pricing"] = combinations

        # Keep selected_* fields useful even for courses created before
        # these fields were added. Derive them from active pricing/package data.
        if not data.get("selected_levels"):
            data["selected_levels"] = sorted({
                item["level"] for item in combinations
            })

        if not data.get("selected_modes"):
            data["selected_modes"] = list(dict.fromkeys(
                item["mode"] for item in combinations
            ))

        if not data.get("selected_lesson_durations"):
            data["selected_lesson_durations"] = list(dict.fromkeys(
                item["lesson_duration"] for item in combinations
            ))

        if not data.get("selected_packages"):
            data["selected_packages"] = list(dict.fromkeys(
                item["package"] for item in combinations
            ))

        return data

    @staticmethod
    def _package_key(package):
        # Prefer the stored count so every package is returned in the same
        # format that the frontend submits, regardless of its display name.
        return f"{package.lesson_count}_lessons"


class LessonTypeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonType
        fields = "__all__"


class LessonDurationSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonDuration
        fields = "__all__"


class LessonModeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonMode
        fields = "__all__"

class LessonTypeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonType
        fields = "__all__"


class LessonDurationSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonDuration
        fields = "__all__"


class LessonModeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LessonMode
        fields = "__all__"


class CoursePricingSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = CoursePricing

        fields = [
            "id",
            "course",
            "lesson_type",
            "duration",
            "mode",
            "level",
            "price",
            "currency",
            "active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "location",
            "location",
        ]

    def validate(self, data):

        course = data.get(
            "course",
            getattr(self.instance, "course", None)
        )

        lesson_type = data.get(
            "lesson_type",
            getattr(
                self.instance,
                "lesson_type",
                None
            )
        )

        duration = data.get(
            "duration",
            getattr(
                self.instance,
                "duration",
                None
            )
        )

        mode = data.get(
            "mode",
            getattr(
                self.instance,
                "mode",
                None
            )
        )

        level = data.get(
            "level",
            getattr(
                self.instance,
                "level",
                None
            )
        )

        existing = CoursePricing.objects.filter(
            course=course,
            lesson_type=lesson_type,
            duration=duration,
            mode=mode,
            level=level
        )

        if self.instance:
            existing = existing.exclude(
                pk=self.instance.pk
            )

        if existing.exists():

            raise serializers.ValidationError({
                "pricing":
                    "This pricing combination already exists."
            })

        return data


class CoursePackageSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = CoursePackage

        fields = [
            "id",
            "course",
            "name",
            "lesson_count",
            "discount_percentage",
            "active",
            "created_at",
            "updated_at",
            "location",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "location",
        ]

class CoursePackagePriceSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = CoursePackagePrice

        fields = [
            "id",
            "package",
            "pricing",
            "price",
            "currency",
            "active",
        ]

        read_only_fields = [
            "id"
        ]


# class EnrollmentSerializer(
#     serializers.ModelSerializer
# ):

#     student_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     course_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     pricing_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     package_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     class Meta:

#         model = Enrollment

#         fields = [
#             "id",
#             "enrollment_number",

#             "student",
#             "student_details",

#             "course",
#             "course_details",

#             "pricing",
#             "pricing_details",

#             "package",
#             "package_details",

#             "total_lessons",
#             "lessons_used",
#             "lessons_remaining",

#             "start_date",
#             "end_date",

#             "total_amount",
#             "status",

#             "created_at",
#             "updated_at",
#         ]

#         read_only_fields = [
#             "id",
#             "enrollment_number",
#             "total_lessons",
#             "lessons_used",
#             "lessons_remaining",
#             "total_amount",
#             "created_at",
#             "updated_at",
#         ]

#     def validate(self, data):

#         pricing = data.get("pricing")

#         package = data.get("package")

#         if pricing and package:

#             if package.course_id != pricing.course_id:

#                 raise serializers.ValidationError({
#                     "package":
#                         "Package does not belong to this course."
#                 })

#         return data

#     def create(self, validated_data):

#         package = validated_data.get("package")

#         pricing = validated_data["pricing"]

#         if package:

#             total_lessons = package.lesson_count

#             package_price = (
#                 CoursePackagePrice.objects
#                 .filter(
#                     package=package,
#                     pricing=pricing,
#                     active=True
#                 )
#                 .first()
#             )

#             if not package_price:

#                 raise serializers.ValidationError({
#                     "package":
#                         "No price configured for this package."
#                 })

#             total_amount = package_price.price

#         else:

#             total_lessons = 1
#             total_amount = pricing.price

#         enrollment = Enrollment.objects.create(
#             **validated_data,
#             total_lessons=total_lessons,
#             lessons_remaining=total_lessons,
#             total_amount=total_amount
#         )

#         return enrollment

#     def get_student_details(self, obj):

#         return {
#             "id": obj.student.id,
#             "name": obj.student.student_name,
#             "student_number":
#                 obj.student.student_number,
#         }

#     def get_course_details(self, obj):

#         return {
#             "id": obj.course.id,
#             "course_name":
#                 obj.course.course_name,
#             "course_number":
#                 obj.course.course_number,
#         }

#     def get_pricing_details(self, obj):

#         return {
#             "id": obj.pricing.id,
#             "level": obj.pricing.level,
#             "price": str(obj.pricing.price),
#             "currency": obj.pricing.currency,

#             "duration":
#                 obj.pricing.duration.minutes,

#             "lesson_type":
#                 obj.pricing.lesson_type.name,

#             "mode":
#                 obj.pricing.mode.name,
#         }

#     def get_package_details(self, obj):

#         if not obj.package:
#             return None

#         return {
#             "id": obj.package.id,
#             "name": obj.package.name,
#             "lesson_count":
#                 obj.package.lesson_count,
#         }


from rest_framework import serializers
from .models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):

    student_details = serializers.SerializerMethodField(read_only=True)
    course_details = serializers.SerializerMethodField(read_only=True)
    pricing_details = serializers.SerializerMethodField(read_only=True)
    package_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "enrollment_number",
            "location",
            "student",
            "student_details",
            "course",
            "course_details",
            "pricing",
            "pricing_details",
            "package",
            "package_details",
            "total_lessons",
            "lessons_used",
            "lessons_remaining",
            "start_date",
            "end_date",
            "registration_fee",
            "total_amount",
            "status",
            "created_at",
            "updated_at",
        ]

        # Removed 'total_amount' from read_only_fields
        read_only_fields = [
            "id",
            "enrollment_number",
            "created_at",
            "updated_at",
            "location",
        ]

    def get_student_details(self, obj):
        return {
            "id": obj.student.id,
            "name": obj.student.student_name,
            "student_number": obj.student.student_number,
            "address": obj.student.address,
        }

    def get_course_details(self, obj):
        return {
            "id": obj.course.id,
            "course_name": obj.course.course_name,
            "course_number": obj.course.course_number,
        }

    def get_pricing_details(self, obj):
        if not obj.pricing:
            return None
        return {
            "id": obj.pricing.id,
            "level": obj.pricing.level,
            "price": str(obj.pricing.price),
            "currency": obj.pricing.currency,
            "duration": obj.pricing.duration.minutes if obj.pricing.duration else None,
            "lesson_type": obj.pricing.lesson_type.name if obj.pricing.lesson_type else None,
            "mode": obj.pricing.mode.name if obj.pricing.mode else None,
        }

    def get_package_details(self, obj):
        if not obj.package:
            return None
        return {
            "id": obj.package.id,
            "name": obj.package.name,
            "lesson_count": obj.package.lesson_count,
        }


# class AppointmentSerializer(
#     serializers.ModelSerializer
# ):

#     enrollment_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     instructor_details = serializers.SerializerMethodField(
#         read_only=True
#     )

#     class Meta:

#         model = Appointment

#         fields = [
#             "id",
#             "appointment_number",

#             "enrollment",
#             "enrollment_details",

#             "instructor",
#             "instructor_details",

#             "lesson",
#             "appointment_date",
#             "start_time",
#             "end_time",

#             "status",
#             "notes",

#             "created_at",
#             "updated_at",
#         ]

#         read_only_fields = [
#             "id",
#             "appointment_number",
#             "enrollment_details",
#             "instructor_details",
#             "created_at",
#             "updated_at",
#         ]

#     def validate(self, data):

#         start_time = data.get(
#             "start_time",
#             getattr(
#                 self.instance,
#                 "start_time",
#                 None
#             )
#         )

#         end_time = data.get(
#             "end_time",
#             getattr(
#                 self.instance,
#                 "end_time",
#                 None
#             )
#         )

#         if start_time and end_time:

#             if start_time >= end_time:

#                 raise serializers.ValidationError({
#                     "end_time":
#                         "End time must be after start time."
#                 })

#         instructor = data.get(
#             "instructor",
#             getattr(
#                 self.instance,
#                 "instructor",
#                 None
#             )
#         )

#         appointment_date = data.get(
#             "appointment_date",
#             getattr(
#                 self.instance,
#                 "appointment_date",
#                 None
#             )
#         )

#         if instructor and appointment_date:

#             conflict = Appointment.objects.filter(
#                 instructor=instructor,
#                 appointment_date=appointment_date,
#                 status__in=[
#                     "requested",
#                     "confirmed"
#                 ]
#             )

#             if self.instance:

#                 conflict = conflict.exclude(
#                     pk=self.instance.pk
#                 )

#             if start_time and end_time:

#                 conflict = conflict.filter(
#                     start_time__lt=end_time,
#                     end_time__gt=start_time
#                 )

#             if conflict.exists():

#                 raise serializers.ValidationError({
#                     "appointment":
#                         "Instructor is already booked during this time."
#                 })

#         enrollment = data.get(
#             "enrollment",
#             getattr(
#                 self.instance,
#                 "enrollment",
#                 None
#             )
#         )

#         if enrollment:

#             if (
#                 enrollment.lessons_remaining <= 0
#                 and not self.instance
#             ):

#                 raise serializers.ValidationError({
#                     "enrollment":
#                         "No lessons remaining in this package."
#                 })

#         return data

#     def get_enrollment_details(self, obj):

#         enrollment = obj.enrollment

#         return {
#             "id": enrollment.id,

#             "student": {
#                 "id": enrollment.student.id,
#                 "name":
#                     enrollment.student.student_name,
#                 "student_number":
#                     enrollment.student.student_number,
#             },

#             "course": {
#                 "id": enrollment.course.id,
#                 "name":
#                     enrollment.course.course_name,
#             },

#             "lessons_remaining":
#                 enrollment.lessons_remaining,

#             "total_lessons":
#                 enrollment.total_lessons,
#         }

#     def get_instructor_details(self, obj):

#         return {
#             "id": obj.instructor.id,
#             "name":
#                 obj.instructor.instructor_name,
#             "instructor_number":
#                 obj.instructor.instructor_number,
#         }


from rest_framework import serializers
from .models import Appointment, AppointmentParticipant, Enrollment, Instructor, Room


class AppointmentParticipantSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="enrollment.student.student_name", read_only=True)
    student_number = serializers.CharField(source="enrollment.student.student_number", read_only=True)
    course_name = serializers.CharField(source="enrollment.course.course_name", read_only=True)

    class Meta:
        model = AppointmentParticipant
        fields = [
            "id",
            "appointment",
            "enrollment",
            "student_name",
            "student_number",
            "course_name",
            "joined_at",
        ]
        read_only_fields = [
            "id",
            "appointment",
            "student_name",
            "student_number",
            "course_name",
            "joined_at",
        ]

class AppointmentSerializer(serializers.ModelSerializer):
    enrollment_details = serializers.SerializerMethodField(read_only=True)
    instructor_details = serializers.SerializerMethodField(read_only=True)
    room_details = serializers.SerializerMethodField(read_only=True)
    participants = AppointmentParticipantSerializer(many=True, read_only=True)
    participant_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_number",
            "location",
            "enrollment",
            "enrollment_details",
            "instructor",
            "instructor_details",
            "room",
            "room_details",
            "participants",
            "participant_count",
            "lesson",
            "appointment_date",
            "start_time",
            "end_time",
            "appointment_type",
            "status",
            "branch_id",
            "branch_name",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "appointment_number",
            "enrollment_details",
            "instructor_details",
            "room_details",
            "participants",
            "participant_count",
            "created_at",
            "updated_at",
            "location",
        ]

    def validate(self, data):
        start_time = data.get("start_time", getattr(self.instance, "start_time", None))
        end_time = data.get("end_time", getattr(self.instance, "end_time", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        instructor = data.get("instructor", getattr(self.instance, "instructor", None))
        appointment_date = data.get("appointment_date", getattr(self.instance, "appointment_date", None))
        room = data.get("room", getattr(self.instance, "room", None))
        appointment_type = data.get(
            "appointment_type",
            getattr(self.instance, "appointment_type", "individual"),
        )

        if room and not room.active:
            raise serializers.ValidationError({"room": "The selected room is inactive."})

        # Check instructor availability conflict
        if instructor and appointment_date and start_time and end_time:
            conflicts = Appointment.objects.filter(
                instructor=instructor,
                appointment_date=appointment_date,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                raise serializers.ValidationError(
                    {"appointment": "The selected instructor is already booked for this time slot."}
                )

        if room and appointment_date and start_time and end_time:
            conflicts = Appointment.objects.filter(
                room=room,
                appointment_date=appointment_date,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                raise serializers.ValidationError(
                    {"room": "The selected room is already booked for this time slot."}
                )

        if appointment_type == "group" and room and room.capacity < 2:
            raise serializers.ValidationError({
                "room": "A group appointment requires a room with capacity for at least two students."
            })

        # Check enrollment lesson availability
        enrollment = data.get("enrollment", getattr(self.instance, "enrollment", None))
        if enrollment and not self.instance:
            if enrollment.lessons_remaining <= 0:
                raise serializers.ValidationError(
                    {"enrollment": "No remaining lessons available in this enrollment package."}
                )

        return data

    def get_enrollment_details(self, obj):
        if not obj.enrollment:
            return None
        return {
            "id": obj.enrollment.id,
            "enrollment_number": obj.enrollment.enrollment_number,
            "student": {
                "id": obj.enrollment.student.id,
                "name": obj.enrollment.student.student_name,
                "student_number": obj.enrollment.student.student_number,
            },
            "course": {
                "id": obj.enrollment.course.id,
                "name": obj.enrollment.course.course_name,
            },
            "lessons_remaining": obj.enrollment.lessons_remaining,
            "total_lessons": obj.enrollment.total_lessons,
        }

    def get_instructor_details(self, obj):
        if not obj.instructor:
            return None
        return {
            "id": obj.instructor.id,
            "name": obj.instructor.instructor_name,
            "instructor_number": obj.instructor.instructor_number,
        }

    def get_room_details(self, obj):
        if not obj.room:
            return None
        return {
            "id": obj.room.id,
            "name": obj.room.name,
            "capacity": obj.room.capacity,
        }

    def get_participant_count(self, obj):
        count = obj.participants.count()
        if count == 0 and obj.enrollment_id:
            return 1
        return count



# ===================================================================== ENROLLED STUDENTS SERIALIZER =====================================================================


class EnrolledStudentSerializer(serializers.ModelSerializer):
    """
    Complete enrolled student details.

    Returns:
    - Full student details
    - Enrollment details
    - Course details
    - Pricing details
    - Package details
    - Appointment details
    """

    student_details = serializers.SerializerMethodField()
    course_details = serializers.SerializerMethodField()
    pricing_details = serializers.SerializerMethodField()
    package_details = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment

        fields = [
            # Enrollment
            "id",
            "enrollment_number",

            # Student
            "student",
            "student_details",

            # Course
            "course",
            "course_details",

            # Pricing
            "pricing",
            "pricing_details",

            # Package
            "package",
            "package_details",

            # Enrollment information
            "total_lessons",
            "lessons_used",
            "lessons_remaining",
            "start_date",
            "end_date",
            "registration_fee",
            "total_amount",
            "status",

            # Appointments
            "appointments",

            # Dates
            "created_at",
            "updated_at",
        ]

    def get_student_details(self, obj):

        student = obj.student

        return {
            "id": student.id,
            "student_number": student.student_number,
            "student_name": student.student_name,
            "date_of_birth": student.date_of_birth,
            "image": (
                student.image.url
                if student.image
                else None
            ),
            "email": student.email,
            "phone": student.phone,
            "emergency_phone": student.emergency_phone,
            "parent_name": student.parent_name,
            "gender": student.gender,
            "branch_id": student.branch_id,
            "branch_name": student.branch_name,
            "relationship": student.relationship,
            "registration_date": student.registration_date,
            "school": student.school,
            "notes": student.notes,
            "active": student.active,
            "payment_status": student.payment_status,
            "course_details": student.course_details,
            "created_at": student.created_at,
            "updated_at": student.updated_at,
        }

    def get_course_details(self, obj):

        course = obj.course

        return {
            "id": course.id,
            "course_number": course.course_number,
            "course_name": course.course_name,
            "category": course.category,
            "description": course.description,
            "level": course.level,
            "selected_levels": course.selected_levels,
            "selected_modes": course.selected_modes,
            "selected_lesson_durations": course.selected_lesson_durations,
            "selected_packages": course.selected_packages,
            "branch_name": obj.location.name if obj.location else None,
            "status": course.status,
            "image": (
                course.image.url
                if course.image
                else None
            ),
            "created_at": course.created_at,
            "updated_at": course.updated_at,
        }

    def get_pricing_details(self, obj):

        pricing = obj.pricing

        if not pricing:
            return None

        return {
            "id": pricing.id,

            "lesson_type": {
                "id": pricing.lesson_type.id,
                "name": pricing.lesson_type.name,
                "code": pricing.lesson_type.code,
                "active": pricing.lesson_type.active,
            },

            "duration": {
                "id": pricing.duration.id,
                "minutes": pricing.duration.minutes,
                "active": pricing.duration.active,
            },

            "mode": {
                "id": pricing.mode.id,
                "name": pricing.mode.name,
                "code": pricing.mode.code,
                "additional_fee": str(
                    pricing.mode.additional_fee
                ),
                "active": pricing.mode.active,
            },

            "level": pricing.level,
            "price": str(pricing.price),
            "currency": pricing.currency,
            "active": pricing.active,

            "created_at": pricing.created_at,
            "updated_at": pricing.updated_at,
        }

    def get_package_details(self, obj):

        package = obj.package

        if not package:
            return None

        package_data = {
            "id": package.id,
            "name": package.name,
            "lesson_count": package.lesson_count,
            "discount_percentage": str(
                package.discount_percentage
            ),
            "active": package.active,
            "created_at": package.created_at,
            "updated_at": package.updated_at,
            "prices": [],
        }

        # Return all pricing combinations for this package
        package_prices = package.prices.select_related(
            "pricing",
            "pricing__lesson_type",
            "pricing__duration",
            "pricing__mode",
        ).filter(active=True)

        for package_price in package_prices:

            pricing = package_price.pricing

            package_data["prices"].append({
                "id": package_price.id,
                "pricing_id": pricing.id,
                "price": str(package_price.price),
                "currency": package_price.currency,
                "active": package_price.active,

                "pricing": {
                    "level": pricing.level,

                    "lesson_type": (
                        pricing.lesson_type.name
                        if pricing.lesson_type
                        else None
                    ),

                    "duration": (
                        pricing.duration.minutes
                        if pricing.duration
                        else None
                    ),

                    "mode": (
                        pricing.mode.name
                        if pricing.mode
                        else None
                    ),
                },
            })

        return package_data

    def get_appointments(self, obj):

        appointments = obj.appointments.select_related(
            "instructor"
        ).all()

        return [
            {
                "id": appointment.id,
                "appointment_number": appointment.appointment_number,

                "lesson": appointment.lesson,

                "appointment_date": appointment.appointment_date,
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,

                "appointment_type": appointment.appointment_type,
                "status": appointment.status,

                "branch_id": appointment.branch_id,
                "branch_name": appointment.branch_name,

                "notes": appointment.notes,

                "instructor": {
                    "id": appointment.instructor.id,
                    "instructor_number": (
                        appointment.instructor.instructor_number
                    ),
                    "instructor_name": (
                        appointment.instructor.instructor_name
                    ),
                    "email": appointment.instructor.email,
                    "phone": appointment.instructor.phone,
                    "specialization": (
                        appointment.instructor.specialization
                    ),
                },

                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at,
            }
            for appointment in appointments
        ]
