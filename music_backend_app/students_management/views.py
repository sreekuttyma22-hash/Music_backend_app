from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction

from .models import (
    Student,
    Location,
    Room,
    Category,
    Instructor,
    Course,
    LessonType,
    LessonDuration,
    LessonMode,
    CoursePricing,
    CoursePackage,
    CoursePackagePrice,
    Enrollment,
    Appointment,
    AppointmentParticipant,
)
from .serializers import (
    EnrolledStudentSerializer,
    LocationSerializer,
    RoomSerializer,
    StudentSerializer,
    CategorySerializer,
    InstructorSerializer,
    CourseSerializer,
    LessonTypeSerializer,
    LessonDurationSerializer,
    LessonModeSerializer,
    CoursePricingSerializer,
    CoursePackageSerializer,
    CoursePackagePriceSerializer,
    EnrollmentSerializer,
    AppointmentSerializer,
    AppointmentParticipantSerializer,
)


class LocationScopedAPIView(APIView):
    """Require the location chosen by the client for branch-owned resources.

    Send it on every scoped request as ``X-Location-ID: <id>``.  The
    ``?location=<id>`` query parameter is also accepted for simple clients.
    """

    def get_location(self, request):
        location_id = (
            request.headers.get("X-Location-ID")
            or request.query_params.get("location")
        )
        if not location_id:
            raise ValidationError({"location": "Select a location first."})
        try:
            return Location.objects.get(pk=location_id, active=True)
        except (Location.DoesNotExist, ValueError, TypeError):
            raise NotFound("Selected location was not found or is inactive.")


class LocationListCreateView(APIView):
    def get(self, request):
        locations = Location.objects.all()
        return Response(LocationSerializer(locations, many=True).data)

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LocationDetailView(APIView):
    def get_object(self, pk):
        try:
            return Location.objects.get(pk=pk)
        except Location.DoesNotExist:
            raise NotFound("Location not found.")

    def get(self, request, pk):
        return Response(LocationSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        serializer = LocationSerializer(self.get_object(pk), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = LocationSerializer(self.get_object(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RoomListCreateView(LocationScopedAPIView):
    def get(self, request):
        rooms = Room.objects.filter(
            location=self.get_location(request),
            active=True,
        )
        return Response(RoomSerializer(rooms, many=True).data)

    def post(self, request):
        location = self.get_location(request)
        serializer = RoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(location=location)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoomDetailView(LocationScopedAPIView):
    def get_object(self, pk, location):
        try:
            return Room.objects.get(pk=pk, location=location)
        except Room.DoesNotExist:
            return None

    def get(self, request, pk):
        room = self.get_object(pk, self.get_location(request))
        if not room:
            raise NotFound("Room not found.")
        return Response(RoomSerializer(room).data)

    def patch(self, request, pk):
        room = self.get_object(pk, self.get_location(request))
        if not room:
            raise NotFound("Room not found.")
        serializer = RoomSerializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        room = self.get_object(pk, self.get_location(request))
        if not room:
            raise NotFound("Room not found.")
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryListCreateView(APIView):
    """List active course categories or create a category."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        categories = Category.objects.filter(active=True).order_by("name")
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentListCreateView(LocationScopedAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        students = Student.objects.filter(location=self.get_location(request))
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(location=self.get_location(request))
            return Response(serializer.data,status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentDetailView(LocationScopedAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk, location):
        try:
            return Student.objects.get(pk=pk, location=location)
        except Student.DoesNotExist:
            return None

    def get(self, request, pk):
        student = self.get_object(pk, self.get_location(request))

        if not student:
            return Response({"error": "Student not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    def put(self, request, pk):
        student = self.get_object(pk, self.get_location(request))
        if not student:
            return Response({"error": "Student not found"},status=status.HTTP_404_NOT_FOUND)

        serializer = StudentSerializer(student,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        student = self.get_object(pk, self.get_location(request))
        if not student:
            return Response({"error": "Student not found"},status=status.HTTP_404_NOT_FOUND)

        serializer = StudentSerializer(student,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        student = self.get_object(pk, self.get_location(request))

        if not student:
            return Response({"error": "Student not found"},status=status.HTTP_404_NOT_FOUND)
        student.delete()

        return Response({"message": "Student deleted successfully"},status=status.HTTP_204_NO_CONTENT)



# ========================== INSTRUCTOR APIS ======================================
from rest_framework.parsers import MultiPartParser, FormParser


class InstructorListCreateView(LocationScopedAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        instructors = Instructor.objects.filter(location=self.get_location(request))
        serializer = InstructorSerializer(instructors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InstructorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(location=self.get_location(request))
            return Response(serializer.data,status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )



class InstructorDetailView(LocationScopedAPIView):
    parser_classes = [MultiPartParser, FormParser]


    def get_object(self, pk, location):
        try:
            return Instructor.objects.get(pk=pk, location=location)
        except Instructor.DoesNotExist:
            return None

    def get(self, request, pk):
        instructor = self.get_object(pk, self.get_location(request))

        if not instructor:
            return Response({"error": "Instructor not found"},status=status.HTTP_404_NOT_FOUND)
        serializer = InstructorSerializer(instructor)
        return Response(serializer.data)

    def put(self, request, pk):
        instructor = self.get_object(pk, self.get_location(request))
        if not instructor:
            return Response({"error": "Instructor not found"},status=status.HTTP_404_NOT_FOUND)

        serializer = InstructorSerializer(instructor,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        instructor = self.get_object(pk, self.get_location(request))
        if not instructor:
            return Response({"error": "Instructor not found"},status=status.HTTP_404_NOT_FOUND)

        serializer = InstructorSerializer(instructor,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        instructor = self.get_object(pk, self.get_location(request))

        if not instructor:
            return Response({"error": "Instructor not found"},status=status.HTTP_404_NOT_FOUND)
        instructor.delete()

        return Response({"message": "Student deleted successfully"},status=status.HTTP_204_NO_CONTENT)





# # =========================================================
# # COURSE LIST + CREATE
# # =========================================================

class CourseListCreateView(APIView):

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]

    def get(self, request):

        courses = (
            Course.objects
            .prefetch_related(
                "instructors",
                "pricing",
                "pricing__lesson_type",
                "pricing__duration",
                "pricing__mode",
                "packages",
                "packages__prices",
                "packages__prices__pricing",
                "packages__prices__pricing__duration",
                "packages__prices__pricing__mode",
            )
            .all()
            .order_by("-created_at")
        )

        serializer = CourseSerializer(
            courses,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = CourseSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# # =========================================================
# # COURSE DETAIL
# # =========================================================

class CourseDetailView(APIView):

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser
    ]

    def get_object(self, pk):

        try:

            return (
                Course.objects
                .prefetch_related(
                    "instructors",
                    "pricing",
                    "pricing__lesson_type",
                    "pricing__duration",
                    "pricing__mode",
                    "packages",
                    "packages__prices",
                    "packages__prices__pricing",
                    "packages__prices__pricing__duration",
                    "packages__prices__pricing__mode",
                )
                .get(pk=pk)
            )

        except Course.DoesNotExist:

            return None

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    def get(self, request, pk):

        course = self.get_object(pk)

        if not course:

            return Response(
                {
                    "error": "Course not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseSerializer(course)

        return Response(serializer.data)

    # -----------------------------------------------------
    # PUT
    # -----------------------------------------------------

    def put(self, request, pk):

        course = self.get_object(pk)

        if not course:

            return Response(
                {
                    "error": "Course not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseSerializer(
            course,
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # PATCH
    # -----------------------------------------------------

    def patch(self, request, pk):

        course = self.get_object(pk)

        if not course:

            return Response(
                {
                    "error": "Course not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseSerializer(
            course,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    def delete(self, request, pk):

        course = self.get_object(pk)

        if not course:

            return Response(
                {
                    "error": "Course not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        course.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


#     # =========================================================
# # COURSE STATISTICS
# # =========================================================

# class CourseStatsView(APIView):

#     def get(self, request):

#         total_courses = Course.objects.count()

#         active_courses = Course.objects.filter(
#             status="active"
#         ).count()

#         # Currently there is no Enrollment model
#         total_enrollments = 0

#         # Currently there is no Enrollment/payment model
#         total_revenue = 0

#         return Response({
#             "total_courses": total_courses,
#             "active_courses": active_courses,
#             "total_enrollments": total_enrollments,
#             "total_revenue": total_revenue,
#         })



class LessonTypeListView(APIView):

    def get(self, request):

        items = LessonType.objects.filter(
            active=True
        )

        serializer = LessonTypeSerializer(
            items,
            many=True
        )

        return Response(serializer.data)

class LessonDurationListView(APIView):

    def get_permissions(self):
            if self.request.method == "GET":
                return [AllowAny()]
            return [IsAuthenticated()]

    def get(self, request):

        items = LessonDuration.objects.filter(
            active=True
        ).order_by("minutes")

        serializer = LessonDurationSerializer(
            items,
            many=True
        )

        return Response(serializer.data)


class LessonModeListView(APIView):
    def get_permissions(self):
            if self.request.method == "GET":
                return [AllowAny()]
            return [IsAuthenticated()]

    def get(self, request):

        items = LessonMode.objects.filter(
            active=True
        )

        serializer = LessonModeSerializer(
            items,
            many=True
        )

        return Response(serializer.data)



# ===================================================================


class CoursePricingListCreateView(APIView):

    def get(self, request):

        course_id = request.query_params.get(
            "course"
        )

        pricing = CoursePricing.objects.select_related(
            "course",
            "lesson_type",
            "duration",
            "mode"
        )

        if course_id:
            pricing = pricing.filter(
                course_id=course_id
            )

        serializer = CoursePricingSerializer(
            pricing,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = CoursePricingSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ====================================================================================
class CoursePackageListCreateView(APIView):

    def get(self, request):

        course_id = request.query_params.get(
            "course"
        )

        packages = CoursePackage.objects.all()

        if course_id:
            packages = packages.filter(
                course_id=course_id
            )

        serializer = CoursePackageSerializer(
            packages,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = CoursePackageSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==============================================================================
class CoursePackagePriceListCreateView(APIView):

    def get(self, request):

        package_id = request.query_params.get(
            "package"
        )

        prices = CoursePackagePrice.objects.select_related(
            "package",
            "pricing"
        )

        if package_id:

            prices = prices.filter(
                package_id=package_id
            )

        serializer = CoursePackagePriceSerializer(
            prices,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = CoursePackagePriceSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# =================================================================================

# class EnrollmentListCreateView(APIView):

#     def get(self, request):

#         enrollments = Enrollment.objects.select_related(
#             "student",
#             "course",
#             "pricing",
#             "package"
#         ).order_by("-created_at")

#         serializer = EnrollmentSerializer(
#             enrollments,
#             many=True
#         )

#         return Response(serializer.data)

#     def post(self, request):

#         serializer = EnrollmentSerializer(
#             data=request.data
#         )

#         if serializer.is_valid():

#             serializer.save()

#             return Response(
#                 serializer.data,
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Enrollment,
    CoursePricing,
    CoursePackagePrice,
)

from .serializers import EnrollmentSerializer


# class EnrollmentListCreateView(APIView):

#     def get(self, request):

#         enrollments = Enrollment.objects.select_related(
#             "student",
#             "course",
#             "pricing",
#             "package"
#         ).order_by("-created_at")

#         serializer = EnrollmentSerializer(
#             enrollments,
#             many=True
#         )

#         return Response(serializer.data)

#     def post(self, request):

#         # --------------------------------------------------
#         # GET VALUES FROM FRONTEND
#         # --------------------------------------------------

#         student_id = request.data.get("student")
#         course_id = request.data.get("course")
#         pricing_amount = request.data.get("pricing")
#         package_id = request.data.get("package")

#         start_date = request.data.get("start_date")
#         end_date = request.data.get("end_date")
#         enrollment_status = request.data.get("status")

#         # --------------------------------------------------
#         # VALIDATE REQUIRED FIELDS
#         # --------------------------------------------------

#         if not student_id:
#             return Response(
#                 {"student": "Student is required."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if not course_id:
#             return Response(
#                 {"course": "Course is required."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         if pricing_amount is None:
#             return Response(
#                 {"pricing": "Pricing amount is required."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # --------------------------------------------------
#         # FIND PRICING USING COURSE + PRICE
#         # --------------------------------------------------

#         try:

#             pricing_amount = Decimal(
#                 str(pricing_amount)
#             )

#         except (ValueError, TypeError):

#             return Response(
#                 {"pricing": "Invalid pricing amount."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         pricing = CoursePricing.objects.filter(
#             course_id=course_id,
#             price=pricing_amount
#         ).first()

#         if not pricing:

#             return Response(
#                 {
#                     "pricing": (
#                         f"No pricing found for course "
#                         f"{course_id} with amount "
#                         f"{pricing_amount}."
#                     )
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # --------------------------------------------------
#         # PACKAGE
#         # --------------------------------------------------

#         package = None

#         if package_id:

#             try:

#                 from .models import CoursePackage

#                 package = CoursePackage.objects.filter(
#                     id=package_id
#                 ).first()

#             except Exception:

#                 return Response(
#                     {
#                         "package":
#                             "Invalid package."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             if not package:

#                 return Response(
#                     {
#                         "package":
#                             "Package does not exist."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # --------------------------------------------------
#             # CHECK PACKAGE BELONGS TO COURSE
#             # --------------------------------------------------

#             if package.course_id != int(course_id):

#                 return Response(
#                     {
#                         "package":
#                             "Package does not belong to this course."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # --------------------------------------------------
#         # CALCULATE LESSONS + TOTAL AMOUNT
#         # --------------------------------------------------

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

#                 return Response(
#                     {
#                         "package":
#                             "No price configured for this "
#                             "package and pricing."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             total_amount = package_price.price

#         else:

#             total_lessons = 1

#             total_amount = pricing.price

#         # --------------------------------------------------
#         # PREPARE DATA FOR SERIALIZER
#         # --------------------------------------------------

#         enrollment_data = {
#             "student": student_id,
#             "course": course_id,

#             # IMPORTANT:
#             # Here we pass the actual Pricing ID,
#             # not 2800
#             "pricing": pricing.id,

#             "start_date": start_date,
#             "end_date": end_date,
#             "status": enrollment_status,

#             "total_lessons": total_lessons,
#             "lessons_used": 0,
#             "lessons_remaining": total_lessons,
#             "total_amount": total_amount,
#         }

#         # Add package only when selected
#         if package:
#             enrollment_data["package"] = package.id
#         else:
#             enrollment_data["package"] = None

#         # --------------------------------------------------
#         # SERIALIZER
#         # --------------------------------------------------

#         serializer = EnrollmentSerializer(
#             data=enrollment_data
#         )

#         if serializer.is_valid():

#             enrollment = serializer.save()

#             return Response(
#                 EnrollmentSerializer(enrollment).data,
#                 status=status.HTTP_201_CREATED
#             )

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

from decimal import Decimal
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Course, CoursePackage, CoursePackagePrice, CoursePricing, Enrollment, Student
from .serializers import EnrollmentSerializer


class EnrollmentListCreateView(LocationScopedAPIView):

    def get(self, request):
        enrollments = Enrollment.objects.filter(location=self.get_location(request)).select_related(
            "student", "course", "pricing", "package"
        ).order_by("-created_at")

        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    def post(self, request):
        location = self.get_location(request)
        # --------------------------------------------------
        # 1. EXTRACT FRONTEND PAYLOAD
        # --------------------------------------------------
        student_id = request.data.get("student")
        course_id = request.data.get("course")
        pricing_amount = request.data.get("pricing")  # Passed as calculated price
        registration_fee_amount = request.data.get("registration_fee", 0)
        package_id = request.data.get("package")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        payment_method = str(request.data.get("payment_method", "")).lower()
        payment_value = request.data.get("payment")

        if isinstance(payment_value, str):
            payment_value = payment_value.lower() in {"true", "1", "yes"}

        payment_completed = (
            payment_value
            if payment_value is not None
            else bool(payment_method)
        )

        if payment_completed and payment_method not in {"cash", "card", "upi", "bank"}:
            return Response(
                {"payment_method": "Choose a valid payment method."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # 2. VALIDATE REQUIRED FIELDS
        # --------------------------------------------------
        if not student_id:
            return Response(
                {"student": "Student is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not course_id:
            return Response(
                {"course": "Course is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pricing_amount is None:
            return Response(
                {"pricing": "Pricing amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_amount = Decimal(str(pricing_amount))
        except (ValueError, TypeError):
            return Response(
                {"pricing": "Invalid pricing amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            registration_fee = Decimal(str(registration_fee_amount))
        except (ValueError, TypeError):
            return Response(
                {"registration_fee": "Invalid registration fee amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if course_amount < 0:
            return Response(
                {"pricing": "Pricing amount cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if registration_fee < 0:
            return Response(
                {"registration_fee": "Registration fee cannot be negative."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Registration is charged once per student.  Never trust a registration
        # fee supplied by the client for a student who has already paid it.
        student = Student.objects.filter(pk=student_id, location=location).first()
        if not student:
            return Response({"student": "Student not found at the selected location."}, status=status.HTTP_400_BAD_REQUEST)

        has_paid_registration_fee = Enrollment.objects.filter(
            location=location,
            student_id=student_id,
            registration_fee__gt=0,
        ).exclude(
            status="cancelled"
        ).exists()

        if has_paid_registration_fee:
            registration_fee = Decimal("0")

        total_amount = course_amount + registration_fee

        # --------------------------------------------------
        # 3. RESOLVE COURSE & PRICING
        # --------------------------------------------------
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response(
                {"course": "Course not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Retrieve a valid default CoursePricing record linked to this course
        pricing = CoursePricing.objects.filter(course=course, active=True).first()

        # Fallback if no specific active pricing rule exists
        if not pricing:
            pricing = CoursePricing.objects.filter(course=course).first()

        if not pricing:
            return Response(
                {"pricing": f"No active pricing model configuration exists for course {course_id}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # 4. RESOLVE PACKAGE & LESSON COUNT
        # --------------------------------------------------
        package = None
        if package_id:
            package = CoursePackage.objects.filter(id=package_id, course_id=course_id).first()
            if not package:
                return Response(
                    {"package": "Selected package does not exist for this course."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            total_lessons = package.lesson_count
        else:
            total_lessons = 1

        # --------------------------------------------------
        # 5. PREPARE DATA & SAVE VIA SERIALIZER
        # --------------------------------------------------
        enrollment_data = {
            "student": student_id,
            "course": course_id,
            "pricing": pricing.id,
            "package": package.id if package else None,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active",
            "total_lessons": total_lessons,
            "lessons_used": 0,
            "lessons_remaining": total_lessons,
            "registration_fee": registration_fee,
            "total_amount": total_amount,
        }

        with transaction.atomic():
            serializer = EnrollmentSerializer(data=enrollment_data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            enrollment = serializer.save(location=location)

            student = Student.objects.select_for_update().get(pk=student_id, location=location)
            student.active = True
            student.payment_status = payment_completed
            student.save(update_fields=["active", "payment_status"])

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )
from django.db.models import Sum


class CourseStatsView(LocationScopedAPIView):

    def get(self, request):
        location = self.get_location(request)

        total_courses = Course.objects.count()

        active_courses = Course.objects.filter(
            status="active"
        ).count()

        total_enrollments = Enrollment.objects.filter(location=location).count()

        total_revenue = (
            Enrollment.objects.filter(location=location)
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        return Response({

            "total_courses":
                total_courses,

            "active_courses":
                active_courses,

            "total_enrollments":
                total_enrollments,

            "total_revenue":
                total_revenue,
        })









from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListCreateView(LocationScopedAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        appointments = (
            Appointment.objects.filter(location=self.get_location(request))
            .select_related(
                "enrollment__student",
                "enrollment__course",
                "instructor",
                "room",
            )
            .prefetch_related(
                "participants__enrollment__student",
                "participants__enrollment__course",
            )
            .all()
            .order_by("-appointment_date", "-start_time")
        )
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        location = self.get_location(request)
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            enrollment = serializer.validated_data.get("enrollment")
            instructor = serializer.validated_data.get("instructor")
            room = serializer.validated_data.get("room")
            if (
                (enrollment and enrollment.location_id != location.id)
                or instructor.location_id != location.id
                or (room and room.location_id != location.id)
            ):
                return Response({"location": "Enrollment and instructor must belong to the selected location."}, status=status.HTTP_400_BAD_REQUEST)
            appointment = serializer.save(location=location)
            if appointment.appointment_type == "group" and enrollment:
                AppointmentParticipant.objects.create(
                    appointment=appointment,
                    enrollment=enrollment,
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentDetailView(LocationScopedAPIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk, location):
        try:
            return (
                Appointment.objects.select_related(
                    "enrollment__student",
                    "enrollment__course",
                    "instructor",
                    "room",
                )
                .prefetch_related(
                    "participants__enrollment__student",
                    "participants__enrollment__course",
                )
                .get(pk=pk, location=location)
            )
        except Appointment.DoesNotExist:
            return None

    def get(self, request, pk):
        appointment = self.get_object(pk, self.get_location(request))
        if not appointment:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        location = self.get_location(request)
        appointment = self.get_object(pk, location)
        if not appointment:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(appointment, data=request.data)
        if serializer.is_valid():
            room = serializer.validated_data.get("room")
            if room and room.location_id != location.id:
                return Response({"room": "Room must belong to the selected location."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        location = self.get_location(request)
        appointment = self.get_object(pk, location)
        if not appointment:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            room = serializer.validated_data.get("room")
            if room and room.location_id != location.id:
                return Response({"room": "Room must belong to the selected location."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        appointment = self.get_object(pk, self.get_location(request))
        if not appointment:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        appointment.delete()
        return Response({"message": "Appointment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class AppointmentParticipantListCreateView(LocationScopedAPIView):
    def get_appointment(self, pk, location):
        try:
            return Appointment.objects.select_related("room").get(
                pk=pk,
                location=location,
            )
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found.")

    def get(self, request, pk):
        appointment = self.get_appointment(pk, self.get_location(request))
        participants = appointment.participants.select_related(
            "enrollment__student",
            "enrollment__course",
        )
        return Response(AppointmentParticipantSerializer(participants, many=True).data)

    def post(self, request, pk):
        location = self.get_location(request)
        appointment = self.get_appointment(pk, location)

        if appointment.appointment_type != "group":
            return Response(
                {"appointment": "Only group appointments can have multiple participants."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not appointment.room:
            return Response(
                {"room": "A group appointment must have a room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant_count = appointment.participants.count()
        if participant_count == 0 and appointment.enrollment_id:
            participant_count = 1
        if participant_count >= appointment.room.capacity:
            return Response(
                {"room": "This room has reached its capacity."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment = Enrollment.objects.select_related("student").filter(
            pk=request.data.get("enrollment"),
            location=location,
            status="active",
        ).first()
        if not enrollment:
            return Response(
                {"enrollment": "Active enrollment not found at the selected location."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if enrollment.lessons_remaining <= 0:
            return Response(
                {"enrollment": "No remaining lessons available in this enrollment package."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if appointment.participants.filter(enrollment=enrollment).exists():
            return Response(
                {"enrollment": "This enrollment is already part of the appointment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if appointment.enrollment_id == enrollment.id:
            return Response(
                {"enrollment": "This enrollment is already part of the appointment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        participant = AppointmentParticipant.objects.create(
            appointment=appointment,
            enrollment=enrollment,
        )
        return Response(
            AppointmentParticipantSerializer(participant).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentParticipantDetailView(LocationScopedAPIView):
    def delete(self, request, pk, participant_pk):
        location = self.get_location(request)
        participant = AppointmentParticipant.objects.filter(
            pk=participant_pk,
            appointment_id=pk,
            appointment__location=location,
        ).first()
        if not participant:
            raise NotFound("Appointment participant not found.")

        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================== ENROLLED STUDENTS ===============================================



class EnrolledStudentsAPIView(LocationScopedAPIView):

    def get(self, request):

        enrollments = (
            Enrollment.objects.filter(location=self.get_location(request))
            .select_related(
                "student",
                "course",
                "location",
                "pricing",
                "pricing__lesson_type",
                "pricing__duration",
                "pricing__mode",
                "package",
            )
            .prefetch_related(
                "appointments__instructor",
                "package__prices__pricing",
                "package__prices__pricing__lesson_type",
                "package__prices__pricing__duration",
                "package__prices__pricing__mode",
            )
            .all()
            .order_by("-created_at")
        )

        serializer = EnrolledStudentSerializer(
            enrollments,
            many=True,
            context={"request": request}
        )

        return Response(
            {
                "success": True,
                "count": enrollments.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK
        )


class EnrollmentDetailView(LocationScopedAPIView):
    """
    Retrieve, update or delete an enrollment instance.
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk, location):
        try:
            return Enrollment.objects.select_related(
                "student", "course", "pricing", "package"
            ).get(pk=pk, location=location)
        except Enrollment.DoesNotExist:
            return None

    def get(self, request, pk):
        enrollment = self.get_object(pk, self.get_location(request))
        if not enrollment:
            return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EnrolledStudentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def put(self, request, pk):
    #     enrollment = self.get_object(pk)
    #     if not enrollment:
    #         return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

    #     serializer = EnrollmentSerializer(enrollment, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def patch(self, request, pk):
    #     enrollment = self.get_object(pk)
    #     if not enrollment:
    #         return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

    #     serializer = EnrollmentSerializer(enrollment, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        enrollment = self.get_object(pk, self.get_location(request))
        if not enrollment:
            return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

        enrollment.delete()
        return Response({"message": "Enrollment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    Student,
    Instructor,
    Course,
    Enrollment,
    Appointment,
)

from datetime import timedelta

from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Student,
    Instructor,
    Course,
    Enrollment,
    Appointment,
)


class DashboardAnalyticsView(LocationScopedAPIView):
    """
    Comprehensive Analytics API providing:
    - Current statistics
    - Last week statistics
    - Last month statistics
    - Last year statistics
    - Course performance
    - Instructor performance
    - Appointment metrics
    - Student demographics
    """

    def get(self, request):

        location = self.get_location(request)

        # ============================================================
        # DATE RANGES
        # ============================================================

        today = timezone.localdate()

        # ------------------------------------------------------------
        # WEEK
        # Monday = 0, Sunday = 6
        # ------------------------------------------------------------

        this_week_start = today - timedelta(days=today.weekday())
        this_week_end = this_week_start + timedelta(days=6)

        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)

        # ------------------------------------------------------------
        # MONTH
        # ------------------------------------------------------------

        this_month_start = today.replace(day=1)

        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        # ------------------------------------------------------------
        # YEAR
        # ------------------------------------------------------------

        this_year_start = today.replace(
            month=1,
            day=1
        )

        last_year_start = this_year_start.replace(
            year=this_year_start.year - 1
        )

        last_year_end = this_year_start - timedelta(days=1)

        # ============================================================
        # 1. SUMMARY - CURRENT VALUES
        # ============================================================

        total_students = Student.objects.filter(
            location=location,
            active=True,
        ).count()

        total_instructors = Instructor.objects.filter(
            location=location,
            status="active"
        ).count()

        total_courses = Course.objects.filter(
            enrollments__location=location,
            status="active"
        ).distinct().count()

        total_enrollments = Enrollment.objects.filter(
            location=location,
            status="active"
        ).count()

        # ============================================================
        # REVENUE
        # ============================================================

        total_revenue = (
            Enrollment.objects
            .filter(location=location)
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        # ============================================================
        # CURRENT PERIOD REVENUE
        # ============================================================

        this_week_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=this_week_start,
                created_at__date__lte=this_week_end
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        this_month_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=this_month_start
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        this_year_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=this_year_start
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        # ============================================================
        # PREVIOUS PERIOD REVENUE
        # ============================================================

        last_week_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=last_week_start,
                created_at__date__lte=last_week_end
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        last_month_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=last_month_start,
                created_at__date__lte=last_month_end
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        last_year_revenue = (
            Enrollment.objects
            .filter(
                location=location,
                created_at__date__gte=last_year_start,
                created_at__date__lte=last_year_end
            )
            .exclude(status="cancelled")
            .aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        # ============================================================
        # 2. ENROLLMENTS BY PERIOD
        # ============================================================

        this_week_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=this_week_start,
            created_at__date__lte=this_week_end
        ).count()

        last_week_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=last_week_start,
            created_at__date__lte=last_week_end
        ).count()

        this_month_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=this_month_start
        ).count()

        last_month_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).count()

        this_year_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=this_year_start
        ).count()

        last_year_enrollments = Enrollment.objects.filter(
            location=location,
            created_at__date__gte=last_year_start,
            created_at__date__lte=last_year_end
        ).count()

        # ============================================================
        # 3. APPOINTMENTS BY PERIOD
        # ============================================================

        appointments_today = Appointment.objects.filter(
            location=location,
            appointment_date=today
        ).count()

        appointments_this_week = Appointment.objects.filter(
            location=location,
            appointment_date__gte=this_week_start,
            appointment_date__lte=this_week_end
        ).count()

        appointments_last_week = Appointment.objects.filter(
            location=location,
            appointment_date__gte=last_week_start,
            appointment_date__lte=last_week_end
        ).count()

        appointments_this_month = Appointment.objects.filter(
            location=location,
            appointment_date__gte=this_month_start
        ).count()

        appointments_last_month = Appointment.objects.filter(
            location=location,
            appointment_date__gte=last_month_start,
            appointment_date__lte=last_month_end
        ).count()

        appointments_this_year = Appointment.objects.filter(
            location=location,
            appointment_date__gte=this_year_start
        ).count()

        appointments_last_year = Appointment.objects.filter(
            location=location,
            appointment_date__gte=last_year_start,
            appointment_date__lte=last_year_end
        ).count()

        # ============================================================
        # 4. APPOINTMENT STATUS
        # ============================================================

        requested_appointments = Appointment.objects.filter(
            location=location,
            status="requested"
        ).count()

        completed_appointments = Appointment.objects.filter(
            location=location,
            status="completed"
        ).count()

        # ============================================================
        # 5. ENROLLMENT BREAKDOWN BY STATUS
        # ============================================================

        enrollments_by_status = dict(
            Enrollment.objects
            .filter(location=location)
            .values_list("status")
            .annotate(count=Count("id"))
        )

        # ============================================================
        # 6. TOP PERFORMING COURSES
        # ============================================================

        top_courses = (
            Course.objects
            .filter(
                enrollments__location=location,
                status="active",
            )
            .annotate(
                active_enrolled=Count(
                    "enrollments",
                    filter=Q(
                        enrollments__location=location,
                        enrollments__status="active"
                    ),
                ),
                total_generated_revenue=Sum(
                    "enrollments__total_amount",
                    filter=Q(enrollments__location=location),
                )
            )
            .distinct()
            .order_by("-active_enrolled")[:5]
        )

        top_courses_data = [
            {
                "id": course.id,
                "course_name": course.course_name,
                "category": course.category,
                "enrolled_students": course.active_enrolled,
                "total_revenue": course.total_generated_revenue or 0,
            }
            for course in top_courses
        ]

        # ============================================================
        # 7. INSTRUCTOR PERFORMANCE
        # ============================================================

        instructors_summary = (
            Instructor.objects
            .filter(location=location)
            .annotate(
                total_appointments=Count(
                    "appointments",
                    filter=Q(appointments__location=location),
                ),
                completed_appointments=Count(
                    "appointments",
                    filter=Q(
                        appointments__location=location,
                        appointments__status="completed"
                    )
                )
            )
            .values(
                "id",
                "instructor_name",
                "specialization",
                "total_appointments",
                "completed_appointments",
            )
            .order_by("-total_appointments")[:5]
        )

        # ============================================================
        # 8. GENDER BREAKDOWN
        # ============================================================

        gender_breakdown = dict(
            Student.objects
            .filter(location=location)
            .values_list("gender")
            .annotate(count=Count("id"))
        )

        # ============================================================
        # 9. RESPONSE
        # ============================================================

        return Response(
            {
                "success": True,

                # ====================================================
                # SUMMARY
                # ====================================================

                "summary": {
                    "total_students": total_students,
                    "total_instructors": total_instructors,
                    "total_active_courses": total_courses,
                    "active_enrollments": total_enrollments,

                    "total_revenue": total_revenue,

                    "revenue": {
                        "this_week": this_week_revenue,
                        "last_week": last_week_revenue,

                        "this_month": this_month_revenue,
                        "last_month": last_month_revenue,

                        "this_year": this_year_revenue,
                        "last_year": last_year_revenue,
                    },

                    "enrollments": {
                        "this_week": this_week_enrollments,
                        "last_week": last_week_enrollments,

                        "this_month": this_month_enrollments,
                        "last_month": last_month_enrollments,

                        "this_year": this_year_enrollments,
                        "last_year": last_year_enrollments,
                    },
                },

                # ====================================================
                # PERIOD COMPARISON
                # ====================================================

                "period_comparison": {
                    "week": {
                        "current": this_week_enrollments,
                        "previous": last_week_enrollments,
                    },

                    "month": {
                        "current": this_month_enrollments,
                        "previous": last_month_enrollments,
                    },

                    "year": {
                        "current": this_year_enrollments,
                        "previous": last_year_enrollments,
                    },
                },

                # ====================================================
                # APPOINTMENTS
                # ====================================================

                "appointments_overview": {
                    "today": appointments_today,

                    "this_week": appointments_this_week,
                    "last_week": appointments_last_week,

                    "this_month": appointments_this_month,
                    "last_month": appointments_last_month,

                    "this_year": appointments_this_year,
                    "last_year": appointments_last_year,

                    "requested": requested_appointments,
                    "completed": completed_appointments,
                },

                # ====================================================
                # COURSES
                # ====================================================

                "top_courses": top_courses_data,

                # ====================================================
                # INSTRUCTORS
                # ====================================================

                "instructors_performance": list(
                    instructors_summary
                ),

                # ====================================================
                # ENROLLMENT STATUS
                # ====================================================

                "enrollment_statuses": enrollments_by_status,

                # ====================================================
                # DEMOGRAPHICS
                # ====================================================

                "student_demographics": {
                    "gender_distribution": gender_breakdown,
                },

                # ====================================================
                # DATE INFORMATION
                # ====================================================

                "periods": {
                    "today": str(today),

                    "this_week": {
                        "start": str(this_week_start),
                        "end": str(this_week_end),
                    },

                    "last_week": {
                        "start": str(last_week_start),
                        "end": str(last_week_end),
                    },

                    "this_month": {
                        "start": str(this_month_start),
                        "end": str(today),
                    },

                    "last_month": {
                        "start": str(last_month_start),
                        "end": str(last_month_end),
                    },

                    "this_year": {
                        "start": str(this_year_start),
                        "end": str(today),
                    },

                    "last_year": {
                        "start": str(last_year_start),
                        "end": str(last_year_end),
                    },
                },
            },
            status=status.HTTP_200_OK,
        )















# ==========================================================LOC API




from rest_framework import generics
from .models import Location
from .serializers import LocationSerializer


class LocationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/locations/  -> List all locations
    POST /api/locations/  -> Create a new location
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/locations/<id>/ -> Get location
    PUT    /api/locations/<id>/ -> Update location
    PATCH  /api/locations/<id>/ -> Partial update
    DELETE /api/locations/<id>/ -> Delete location
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer