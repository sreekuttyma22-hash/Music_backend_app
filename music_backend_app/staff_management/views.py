from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Staff

from .serializers import (
    StaffSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer
)

from .authentication import (
    StaffJWTAuthentication
)


class IsAdminStaff(IsAuthenticated):
    """Allow only an authenticated, approved administrator staff account."""

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and getattr(request.user, "is_admin", False)
            and getattr(request.user, "admin_enabled", False)
            and getattr(request.user, "is_active", False)
        )


# =========================================================
# STAFF LIST + CREATE
# =========================================================

class StaffListCreateView(APIView):

    authentication_classes = [StaffJWTAuthentication]
    permission_classes = [IsAdminStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # -----------------------------------------------------
    # GET - LIST ALL STAFF
    # -----------------------------------------------------

    def get(self, request):

        staffs = Staff.objects.all().order_by(
            '-id'
        )

        serializer = StaffSerializer(
            staffs,
            many=True
        )

        return Response({

            'success': True,

            'count': staffs.count(),

            'results': serializer.data

        })


    # -----------------------------------------------------
    # POST - CREATE STAFF
    # -----------------------------------------------------

    def post(self, request):

        serializer = StaffCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():

            staff = serializer.save()

            return Response(

                {
                    'success': True,

                    'message':
                        'Staff created successfully.',

                    'result':
                        StaffSerializer(
                            staff
                        ).data
                },

                status=status.HTTP_201_CREATED
            )

        return Response(

            {
                'success': False,

                'errors':
                    serializer.errors
            },

            status=status.HTTP_400_BAD_REQUEST
        )


class StaffDetailView(APIView):
    """Custom admin-only endpoint for one staff member."""

    authentication_classes = [StaffJWTAuthentication]
    permission_classes = [IsAdminStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return None

    def get(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response(
                {"success": False, "message": "Staff member not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "success": True,
            "result": StaffSerializer(staff).data,
        })

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        staff = self.get_object(pk)
        if not staff:
            return Response(
                {"success": False, "message": "Staff member not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StaffUpdateSerializer(
            staff,
            data=request.data,
            partial=partial,
        )
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        staff = serializer.save()
        return Response({
            "success": True,
            "message": "Staff updated successfully.",
            "result": StaffSerializer(staff).data,
        })

    def delete(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response(
                {"success": False, "message": "Staff member not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        staff.delete()
        return Response({
            "success": True,
            "message": "Staff deleted successfully.",
        })


# =========================================================
# STAFF DETAIL
# =========================================================

# class StaffDetailView(APIView):

#     authentication_classes = [
#         StaffJWTAuthentication
#     ]

#     permission_classes = [
#         IsAuthenticated
#     ]


#     # -----------------------------------------------------
#     # GET STAFF OBJECT
#     # -----------------------------------------------------

#     def get_object(self, pk):

#         try:

#             return Staff.objects.get(
#                 pk=pk
#             )

#         except Staff.DoesNotExist:

#             return None


#     # -----------------------------------------------------
#     # GET SINGLE STAFF
#     # -----------------------------------------------------

#     def get(self, request, pk):

#         staff = self.get_object(pk)

#         if not staff:

#             return Response(

#                 {
#                     'success': False,

#                     'message':
#                         'Staff not found.'
#                 },

#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = StaffSerializer(
#             staff
#         )

#         return Response({

#             'success': True,

#             'result': serializer.data

#         })


#     # -----------------------------------------------------
#     # PUT - UPDATE STAFF
#     # -----------------------------------------------------

#     def put(self, request, pk):

#         staff = self.get_object(pk)

#         if not staff:

#             return Response(

#                 {
#                     'success': False,

#                     'message':
#                         'Staff not found.'
#                 },

#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = StaffUpdateSerializer(

#             staff,

#             data=request.data
#         )

#         if serializer.is_valid():

#             staff = serializer.save()

#             return Response({

#                 'success': True,

#                 'message':
#                     'Staff updated successfully.',

#                 'result':
#                     StaffSerializer(
#                         staff
#                     ).data

#             })

#         return Response(

#             {
#                 'success': False,

#                 'errors':
#                     serializer.errors
#             },

#             status=status.HTTP_400_BAD_REQUEST
#         )


#     # -----------------------------------------------------
#     # PATCH - PARTIAL UPDATE
#     # -----------------------------------------------------

#     def patch(self, request, pk):

#         staff = self.get_object(pk)

#         if not staff:

#             return Response(

#                 {
#                     'success': False,

#                     'message':
#                         'Staff not found.'
#                 },

#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = StaffUpdateSerializer(

#             staff,

#             data=request.data,

#             partial=True
#         )

#         if serializer.is_valid():

#             staff = serializer.save()

#             return Response({

#                 'success': True,

#                 'message':
#                     'Staff updated successfully.',

#                 'result':
#                     StaffSerializer(
#                         staff
#                     ).data

#             })

#         return Response(

#             {
#                 'success': False,

#                 'errors':
#                     serializer.errors
#             },

#             status=status.HTTP_400_BAD_REQUEST
#         )


#     # -----------------------------------------------------
#     # DELETE STAFF
#     # -----------------------------------------------------

#     def delete(self, request, pk):

#         staff = self.get_object(pk)

#         if not staff:

#             return Response(

#                 {
#                     'success': False,

#                     'message':
#                         'Staff not found.'
#                 },

#                 status=status.HTTP_404_NOT_FOUND
#             )

#         staff.delete()

#         return Response({

#             'success': True,

#             'message':
#                 'Staff deleted successfully.'

#         })


# =========================================================
# STAFF LOGIN
# =========================================================

class StaffLoginView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        email = request.data.get(
            'email'
        )

        password = request.data.get(
            'password'
        )


        # -------------------------------------------------
        # VALIDATE INPUT
        # -------------------------------------------------

        if not email or not password:

            return Response(

                {
                    'success': False,

                    'message':
                        'Email and password are required.'
                },

                status=status.HTTP_400_BAD_REQUEST
            )


        # -------------------------------------------------
        # FIND STAFF
        # -------------------------------------------------

        try:

            staff = Staff.objects.get(
                email=email
            )

        except Staff.DoesNotExist:

            return Response(

                {
                    'success': False,

                    'message':
                        'Invalid email or password.'
                },

                status=status.HTTP_401_UNAUTHORIZED
            )


        # -------------------------------------------------
        # ACTIVE CHECK
        # -------------------------------------------------

        if not staff.is_active:

            return Response(

                {
                    'success': False,

                    'message':
                        'Your account is inactive.'
                },

                status=status.HTTP_403_FORBIDDEN
            )

        if not staff.admin_enabled:
            return Response(
                {
                    'success': False,
                    'message': 'Your account is awaiting administrator approval.'
                },
                status=status.HTTP_403_FORBIDDEN
            )


        # -------------------------------------------------
        # PASSWORD CHECK
        # -------------------------------------------------

        if not staff.check_password(
            password
        ):

            return Response(

                {
                    'success': False,

                    'message':
                        'Invalid email or password.'
                },

                status=status.HTTP_401_UNAUTHORIZED
            )


        # -------------------------------------------------
        # CREATE JWT
        # -------------------------------------------------

        refresh = RefreshToken()

        refresh['staff_id'] = staff.id

        refresh['email'] = staff.email

        access_token = refresh.access_token

        return Response({

            'success': True,

            'message':
                'Login successful.',

            'access':
                str(access_token),

            'refresh':
                str(refresh),

            'staff':
                StaffSerializer(
                    staff
                ).data

        })


# =========================================================
# STAFF LOGOUT
# =========================================================

class StaffLogoutView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        refresh_token = request.data.get(
            'refresh'
        )

        if not refresh_token:

            return Response(

                {
                    'success': False,

                    'message':
                        'Refresh token is required.'
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(
                refresh_token
            )

            token.blacklist()

            return Response({

                'success': True,

                'message':
                    'Logout successful.'

            })

        except TokenError:

            return Response(

                {
                    'success': False,

                    'message':
                        'Invalid or expired refresh token.'
                },

                status=status.HTTP_400_BAD_REQUEST
            )


# =========================================================
# CURRENT LOGGED-IN STAFF
# =========================================================

class StaffMeView(APIView):

    authentication_classes = [
        StaffJWTAuthentication
    ]

    

    def get(self, request):

        staff = request.user

        serializer = StaffSerializer(
            staff
        )

        return Response({

            'success': True,

            'result':
                serializer.data

        })



class StaffRegisterView(APIView):

    permission_classes = [
        AllowAny
    ]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):

        data = request.data.copy()

        # Public registration must not enable accounts directly
        data.pop("admin_enabled", None)
        data.pop("is_active", None)
        data.pop("is_admin", None)

        serializer = StaffCreateSerializer(data=data)

        if serializer.is_valid():

            staff = serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Staff registration successful. Wait for admin approval.",
                    "result": StaffSerializer(staff).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class StaffApprovalView(APIView):
    authentication_classes = [StaffJWTAuthentication]
    permission_classes = [IsAdminStaff]

    def patch(self, request, pk):
        try:
            staff = Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return Response(
                {"success": False, "message": "Staff member not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        approved = request.data.get("admin_enabled")
        if isinstance(approved, str):
            approved = approved.lower() in {"true", "1", "yes"}

        if not isinstance(approved, bool):
            return Response(
                {
                    "success": False,
                    "message": "admin_enabled must be a boolean.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        staff.admin_enabled = approved
        if "is_active" in request.data:
            active = request.data["is_active"]
            if isinstance(active, str):
                active = active.lower() in {"true", "1", "yes"}
            if not isinstance(active, bool):
                return Response(
                    {"success": False, "message": "is_active must be a boolean."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            staff.is_active = active

        staff.save(update_fields=["admin_enabled", "is_active", "updated_at"])

        return Response({
            "success": True,
            "message": "Staff approval updated successfully.",
            "result": StaffSerializer(staff).data,
        })


# STAFF REFRESH TOKEN
# =========================================================

class StaffRefreshTokenView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        refresh_token = request.data.get(
            'refresh'
        )

        if not refresh_token:

            return Response(

                {
                    'success': False,

                    'message':
                        'Refresh token is required.'
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            token = RefreshToken(
                refresh_token
            )

            access_token = token.access_token

            return Response({

                'success': True,

                'message':
                    'Token refreshed successfully.',

                'access':
                    str(access_token),

            })

        except TokenError:

            return Response(

                {
                    'success': False,

                    'message':
                        'Invalid or expired refresh token.'
                },

                status=status.HTTP_401_UNAUTHORIZED
            )