from django.contrib import admin
from .models import Location, Room, Student, Instructor, Appointment, AppointmentParticipant, Category, Course, LessonType, LessonDuration, LessonMode, CoursePricing,CoursePackage, CoursePackagePrice, Enrollment

# Register your models here.

admin.site.register(Student)
admin.site.register(Location)
admin.site.register(Room)
admin.site.register(Instructor)
admin.site.register(Appointment)
admin.site.register(AppointmentParticipant)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(LessonType)
admin.site.register(LessonDuration)
admin.site.register(LessonMode)
admin.site.register(CoursePricing)
admin.site.register(CoursePackage)
admin.site.register(CoursePackagePrice)
admin.site.register(Enrollment)
