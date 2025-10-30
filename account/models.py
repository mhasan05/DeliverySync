from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.utils import timezone
from account.manager import UserManager #import from account apps



class UserAuth(AbstractBaseUser,PermissionsMixin):
    class Meta:
        verbose_name_plural = "User"
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('company', 'Company'),
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=100,unique=True)
    image = models.ImageField(upload_to='profile_images', default='profile_images/default.jpg',null=True,blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address = models.TextField(blank=True)
    location_latitude = models.CharField(max_length=255,blank=True)
    location_longitude = models.CharField(max_length=255,blank=True)
    vehicle = models.CharField(max_length=20, blank=True)
    vehicle_registration_number = models.CharField(max_length=20, blank=True)
    driving_license_number = models.CharField(max_length=20, blank=True)
    default_delivery_fee = models.FloatField(default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expired = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    login_streak = models.IntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name','role']

    objects = UserManager()

    def __str__(self):
        return self.name