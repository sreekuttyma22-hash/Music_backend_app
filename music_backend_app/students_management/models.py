from django.db import models

# Create your models here.


class Location(models.Model):
    """A physical branch/campus that owns operational data."""

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=30, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Room(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="rooms",
    )
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["location", "name"],
                name="unique_room_per_location",
            )
        ]
        ordering = ["location", "name"]

    def __str__(self):
        return f"{self.location.code} - {self.name}"


class Student(models.Model):
    GENDER_CHOICES = [ ("male", "Male"), 
                      ("female", "Female"), 
                      ("other", "Other"),]

    RELATIONSHIP_CHOICES = [ ("Father", "Father"), 
                            ("Mother", "Mother"), 
                            ("Guardian", "Guardian"), 
                            ("Other", "Other"),]

    student_number = models.CharField( max_length=50, unique=True, blank=True, editable=False)
    student_name = models.CharField( max_length=255, blank=True, null=True)
    date_of_birth = models.DateField( null=True, blank=True)
    image = models.ImageField( upload_to="students/", null=True, blank=True)
    email = models.EmailField( blank=True, null=True)
    phone = models.CharField( max_length=20, blank=True, null=True)
    address = models.TextField( blank=True, null=True)
    emergency_phone = models.CharField( max_length=20, blank=True, null=True)
    parent_name = models.CharField( max_length=255, blank=True, null=True)
    gender = models.CharField( max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="students", null=True, blank=True)
    # Legacy fields are retained temporarily so existing client payloads and records remain readable.
    branch_id = models.IntegerField( null=True, blank=True)
    branch_name = models.CharField( max_length=255, blank=True, null=True)
    relationship = models.CharField( max_length=50, choices=RELATIONSHIP_CHOICES, blank=True, null=True)
    registration_date = models.DateField( null=True, blank=True)
    school = models.CharField( max_length=255, blank=True, null=True)
    notes = models.TextField( blank=True, null=True)
    active = models.BooleanField(default=False)
    payment_status = models.BooleanField(default=False)
    course_details = models.JSONField( blank=True, null=True)

    created_at = models.DateTimeField( auto_now_add=True)
    updated_at = models.DateTimeField( auto_now=True)

    def save(self, *args, **kwargs):
            # First save to generate the database ID
            super().save(*args, **kwargs)
            # Generate student number from ID
            if not self.student_number:
                self.student_number = f"STU-{self.id:05d}"
                super().save(update_fields=["student_number"])

    def __str__(self): return f"{self.student_number} - {self.student_name}"




# ----------------------- INSTRUCTOR MODEL ----------------------------------


class Instructor(models.Model):

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    EMPLOYMENT_CHOICES = [
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("contract", "Contract"),
        ("visiting", "Visiting"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("on_leave", "On Leave"),
    ]

    instructor_number = models.CharField(max_length=50,unique=True,blank=True,editable=False)
    instructor_name = models.CharField(max_length=100,blank=True,null=True)
    profile_image = models.ImageField(upload_to="instructors/",blank=True,null=True)
    date_of_birth = models.DateField(blank=True,null=True)
    gender = models.CharField(max_length=20,choices=GENDER_CHOICES,blank=True,null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    emergency_contact_name = models.CharField(max_length=255,blank=True,null=True)
    emergency_contact_phone = models.CharField(max_length=20,blank=True,null=True)
    address = models.TextField(blank=True,null=True)
    qualification = models.CharField(max_length=255,blank=True,null=True)
    specialization = models.CharField(max_length=255,blank=True,null=True)
    experience_years = models.PositiveIntegerField(default=0)
    instruments = models.CharField(max_length=255,blank=True,null=True)
    bio = models.TextField(blank=True,null=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="instructors", null=True, blank=True)
    # Legacy fields are retained temporarily so existing client payloads and records remain readable.
    branch_id = models.IntegerField(null=True,blank=True)
    branch_name = models.CharField(max_length=255,blank=True,null=True)
    joining_date = models.DateField(blank=True,null=True)
    employment_type = models.CharField(max_length=20,choices=EMPLOYMENT_CHOICES,default="full_time")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="active")
    availability = models.CharField(max_length=255,blank=True,null=True)  
    notes = models.TextField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # First save to generate the database ID
        super().save(*args, **kwargs)
        # Generate instructor number from ID
        if not self.instructor_number:
            self.instructor_number = f"INS-{self.id:05d}"
            super().save(update_fields=["instructor_number"])

    def __str__(self):
        return f"{self.instructor_number} - {self.instructor_name} "



# ========================== COURSE CATEGORY MODEL ==========================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


# ========================== COURSE MODEL ==========================

class Course(models.Model):

    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("draft", "Draft"),
    ]

    course_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
    )

    course_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Kept for backward compatibility with existing data.
    # The CoursesPage supports multiple levels through selected_levels.
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="beginner",
    )

    # Configuration selected on CoursesPage.
    # Actual prices remain normalized in CoursePricing and
    # CoursePackagePrice.
    selected_levels = models.JSONField(default=list, blank=True)
    selected_modes = models.JSONField(default=list, blank=True)
    selected_lesson_durations = models.JSONField(default=list, blank=True)
    selected_packages = models.JSONField(default=list, blank=True)

    instructors = models.ManyToManyField(
        Instructor,
        related_name="courses",
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    image = models.ImageField(upload_to="courses/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.course_number:
            self.course_number = f"CRS-{self.id:05d}"
            super().save(update_fields=["course_number"])

    def __str__(self):
        return f"{self.course_number} - {self.course_name}"


class LessonType(models.Model):

    TYPE_CHOICES = [
        ("private", "Private"),
        ("group", "Group"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20,choices=TYPE_CHOICES,unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class LessonDuration(models.Model):

    minutes = models.PositiveIntegerField(unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.minutes} Minutes"
    

class LessonMode(models.Model):

    MODE_CHOICES = [
        ("institute", "Institute"),
        ("online", "Online"),
        ("home_visit", "Home Visit"),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30,choices=MODE_CHOICES,unique=True)
    additional_fee = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CoursePricing(models.Model):

    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name="pricing")
    lesson_type = models.ForeignKey(LessonType,on_delete=models.PROTECT,related_name="course_pricing")
    duration = models.ForeignKey(LessonDuration,on_delete=models.PROTECT,related_name="course_pricing")
    mode = models.ForeignKey(LessonMode,on_delete=models.PROTECT,related_name="course_pricing")
    level = models.CharField(max_length=20,choices=Course.LEVEL_CHOICES,default="beginner")
    price = models.DecimalField(max_digits=10,decimal_places=2)
    currency = models.CharField(max_length=10,default="OMR")
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "course",
                    "lesson_type",
                    "duration",
                    "mode",
                    "level"
                ],
                name="unique_course_pricing"
            )
        ]

    def __str__(self):

        return (
            f"{self.course.course_name} - "
            f"{self.lesson_type.name} - "
            f"{self.duration.minutes} min - "
            f"{self.mode.name} - "
            f"{self.level}"
        )


class CoursePackage(models.Model):

    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name="packages")
    name = models.CharField(max_length=100)
    lesson_count = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(max_digits=5,decimal_places=2,default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return (
            f"{self.course.course_name} - "
            f"{self.name}"
        )

class CoursePackagePrice(models.Model):

    package = models.ForeignKey(CoursePackage,on_delete=models.CASCADE,related_name="prices")
    pricing = models.ForeignKey(CoursePricing,on_delete=models.CASCADE,related_name="package_prices")
    price = models.DecimalField(max_digits=10,decimal_places=2)
    currency = models.CharField(max_length=10,default="OMR")

    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "package",
                    "pricing"
                ],
                name="unique_package_pricing"
            )
        ]

    def __str__(self):

        return (
            f"{self.package.name} - "
            f"{self.pricing}"
        )


class Enrollment(models.Model):

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("paused", "Paused"),
    ]

    enrollment_number = models.CharField(max_length=50,unique=True,blank=True,editable=False)
    student = models.ForeignKey(Student,on_delete=models.CASCADE,related_name="enrollments")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="enrollments", null=True, blank=True)
    course = models.ForeignKey(Course,on_delete=models.PROTECT,related_name="enrollments")
    pricing = models.ForeignKey(CoursePricing,on_delete=models.PROTECT,related_name="enrollments")
    package = models.ForeignKey(CoursePackage,on_delete=models.PROTECT,related_name="enrollments",null=True,blank=True)
    total_lessons = models.PositiveIntegerField()
    lessons_used = models.PositiveIntegerField(default=0)
    lessons_remaining = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True,blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="active")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        if not self.enrollment_number:

            super().save(*args, **kwargs)

            self.enrollment_number = (
                f"ENR-{self.id:05d}"
            )

            super().save(
                update_fields=["enrollment_number"]
            )

        else:
            super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.enrollment_number} - "
            f"{self.student.student_name}"
        )




class Appointment(models.Model):

    APPOINTMENT_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("group", "Group"),
    ]

    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("requested", "Requested"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    appointment_number = models.CharField(max_length=50,unique=True,blank=True,editable=False)
    enrollment = models.ForeignKey(Enrollment,on_delete=models.CASCADE,related_name="appointments",null=True,blank=True)
    instructor = models.ForeignKey(Instructor,on_delete=models.CASCADE,related_name="appointments")
    lesson = models.CharField(max_length=255)
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(max_length=20,choices=APPOINTMENT_TYPE_CHOICES,default="individual")
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="requested")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="appointments", null=True, blank=True)
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
    )
    # Legacy fields are retained temporarily so existing client payloads and records remain readable.
    branch_id = models.IntegerField(null=True,blank=True)
    branch_name = models.CharField(max_length=255,blank=True,null=True)
    notes = models.TextField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.appointment_number:
            self.appointment_number = f"APT-{self.id:05d}"

            super().save(
                update_fields=["appointment_number"]
            )

    def __str__(self):
        return (
            f"{self.appointment_number} - "
            f"{self.enrollment.student.student_name if self.enrollment else self.lesson} - "
            f"{self.appointment_date}"
        )


class AppointmentParticipant(models.Model):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="appointment_participations",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["appointment", "enrollment"],
                name="unique_appointment_participant",
            )
        ]

    def __str__(self):
        return f"{self.appointment} - {self.enrollment}"

