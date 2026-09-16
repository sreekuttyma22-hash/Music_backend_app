from django.urls import path

from .views import (
    StaffListCreateView,
    StaffRegisterView,
    StaffLoginView,
    StaffLogoutView,
    StaffMeView,
    StaffRefreshTokenView,
    StaffApprovalView,
    StaffDetailView,
)

urlpatterns = [
    # Protected staff list/create endpoint
    path(
        "",
        StaffListCreateView.as_view(),
        name="staff-list-create",
    ),

    # Public staff registration endpoint
    path(
        "create/",
        StaffRegisterView.as_view(),
        name="staff-register",
    ),

    path(
        "login/",
        StaffLoginView.as_view(),
        name="staff-login",
    ),

    path(
        "logout/",
        StaffLogoutView.as_view(),
        name="staff-logout",
    ),

    path(
        "me/",
        StaffMeView.as_view(),
        name="staff-me",
    ),

    path(
        "refresh/",
        StaffRefreshTokenView.as_view(),
        name="staff-refresh-token",
    ),
    path(
        "<int:pk>/",
        StaffDetailView.as_view(),
        name="staff-detail",
    ),
    path(
        "<int:pk>/approval/",
        StaffApprovalView.as_view(),
        name="staff-approval",
    ),
]