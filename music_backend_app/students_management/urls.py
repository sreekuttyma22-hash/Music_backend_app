from django.urls import path

from .views import (
    AppointmentDetailView,
    AppointmentListCreateView,
    CourseListCreateView,
    CourseDetailView,
    CourseStatsView,
    DashboardAnalyticsView,
    EnrolledStudentsAPIView,
    EnrollmentDetailView,
    StudentListCreateView,
    StudentDetailView,
    InstructorListCreateView,
    InstructorDetailView,
    LessonTypeListView,
    LessonDurationListView,
    LessonModeListView,
    CoursePricingListCreateView,
    CoursePackageListCreateView,
    CoursePackagePriceListCreateView,
    EnrollmentListCreateView,
    CategoryListCreateView,
    LocationListCreateView,
    LocationDetailView,
    RoomListCreateView,
    RoomDetailView,
    AppointmentParticipantListCreateView,
    AppointmentParticipantDetailView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),

    # COURSES
    path(
        "courses/",
        CourseListCreateView.as_view(),
        name="course-list-create",
    ),
    path(
        "courses/<int:pk>/",
        CourseDetailView.as_view(),
        name="course-detail",
    ),
    path(
        "courses/stats/",
        CourseStatsView.as_view(),
        name="course-stats",
    ),

    # PRICING OPTIONS
    path(
        "lesson-types/",
        LessonTypeListView.as_view(),
        name="lesson-types",
    ),
    path(
        "lesson-durations/",
        LessonDurationListView.as_view(),
        name="lesson-durations",
    ),
    path(
        "lesson-modes/",
        LessonModeListView.as_view(),
        name="lesson-modes",
    ),

    # COURSE PRICING
    path(
        "course-pricing/",
        CoursePricingListCreateView.as_view(),
        name="course-pricing",
    ),

    # PACKAGES
    path(
        "course-packages/",
        CoursePackageListCreateView.as_view(),
        name="course-packages",
    ),
    path(
        "course-package-prices/",
        CoursePackagePriceListCreateView.as_view(),
        name="course-package-prices",
    ),

    # ENROLLMENTS
    path(
        "enrollments/",
        EnrollmentListCreateView.as_view(),
        name="enrollments",
    ),

    # STUDENTS
    path(
        "students/",
        StudentListCreateView.as_view(),
        name="student-list-create",
    ),
    path(
        "students/<int:pk>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),

    # INSTRUCTORS
    path(
        "instructors/",
        InstructorListCreateView.as_view(),
        name="instructor-list-create",
    ),
    path(
        "instructors/<int:pk>/",
        InstructorDetailView.as_view(),
        name="instructor-detail",
    ),

    #APPOINTMENTS
    path("appointments/",AppointmentListCreateView.as_view(),name="appointment-list-create"),
    path("appointments/<int:pk>/",AppointmentDetailView.as_view(),name="appointment-detail"),
    path(
        "appointments/<int:pk>/participants/",
        AppointmentParticipantListCreateView.as_view(),
        name="appointment-participant-list-create",
    ),
    path(
        "appointments/<int:pk>/participants/<int:participant_pk>/",
        AppointmentParticipantDetailView.as_view(),
        name="appointment-participant-detail",
    ),
    path(
        "enrolled-students/",
        EnrolledStudentsAPIView.as_view(),
        name="enrolled-students"
    ),
    path(
        "enrolled-students/<int:pk>/",
        EnrollmentDetailView.as_view(),
        name="enrollment-detail",
    ),


    path(
        "analytics/dashboard/",
        DashboardAnalyticsView.as_view(),
        name="dashboard-analytics",
    ),


    # ================================
    path(
        "locations/",
        LocationListCreateView.as_view(),
        name="location-list-create"
    ),

    path(
        "locations/<int:pk>/",
        LocationDetailView.as_view(),
        name="location-detail"
    ),
    path(
        "rooms/",
        RoomListCreateView.as_view(),
        name="room-list-create",
    ),
    path(
        "rooms/<int:pk>/",
        RoomDetailView.as_view(),
        name="room-detail",
    ),
]

