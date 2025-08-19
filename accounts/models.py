from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    COUNTRY_CHOICES = (
        ("UK", "United Kingdom"),
        ("Other", "Other"),
    )
    country = models.CharField(
        max_length=32,
        choices=COUNTRY_CHOICES,
        default="UK",
        help_text="Country of residence."
    )

    UK_COUNTY_CHOICES = (
        # England
        ("Bedfordshire", "Bedfordshire"),
        ("Berkshire", "Berkshire"),
        ("Bristol", "Bristol"),
        ("Buckinghamshire", "Buckinghamshire"),
        ("Cambridgeshire", "Cambridgeshire"),
        ("Cheshire", "Cheshire"),
        ("City of London", "City of London"),
        ("Cornwall", "Cornwall"),
        ("Cumbria", "Cumbria"),
        ("Derbyshire", "Derbyshire"),
        ("Devon", "Devon"),
        ("Dorset", "Dorset"),
        ("Durham", "Durham"),
        ("East Riding of Yorkshire", "East Riding of Yorkshire"),
        ("East Sussex", "East Sussex"),
        ("Essex", "Essex"),
        ("Gloucestershire", "Gloucestershire"),
        ("Greater London", "Greater London"),
        ("Greater Manchester", "Greater Manchester"),
        ("Hampshire", "Hampshire"),
        ("Herefordshire", "Herefordshire"),
        ("Hertfordshire", "Hertfordshire"),
        ("Isle of Wight", "Isle of Wight"),
        ("Kent", "Kent"),
        ("Lancashire", "Lancashire"),
        ("Leicestershire", "Leicestershire"),
        ("Lincolnshire", "Lincolnshire"),
        ("Merseyside", "Merseyside"),
        ("Norfolk", "Norfolk"),
        ("North Yorkshire", "North Yorkshire"),
        ("Northamptonshire", "Northamptonshire"),
        ("Northumberland", "Northumberland"),
        ("Nottinghamshire", "Nottinghamshire"),
        ("Oxfordshire", "Oxfordshire"),
        ("Rutland", "Rutland"),
        ("Shropshire", "Shropshire"),
        ("Somerset", "Somerset"),
        ("South Yorkshire", "South Yorkshire"),
        ("Staffordshire", "Staffordshire"),
        ("Suffolk", "Suffolk"),
        ("Surrey", "Surrey"),
        ("Tyne and Wear", "Tyne and Wear"),
        ("Warwickshire", "Warwickshire"),
        ("West Midlands", "West Midlands"),
        ("West Sussex", "West Sussex"),
        ("West Yorkshire", "West Yorkshire"),
        ("Wiltshire", "Wiltshire"),
        ("Worcestershire", "Worcestershire"),
        # Wales
        ("Anglesey", "Anglesey"),
        ("Brecknockshire", "Brecknockshire"),
        ("Caernarfonshire", "Caernarfonshire"),
        ("Cardiganshire", "Cardiganshire"),
        ("Carmarthenshire", "Carmarthenshire"),
        ("Clwyd", "Clwyd"),
        ("Denbighshire", "Denbighshire"),
        ("Flintshire", "Flintshire"),
        ("Glamorgan", "Glamorgan"),
        ("Merionethshire", "Merionethshire"),
        ("Monmouthshire", "Monmouthshire"),
        ("Montgomeryshire", "Montgomeryshire"),
        ("Pembrokeshire", "Pembrokeshire"),
        ("Powys", "Powys"),
        ("Radnorshire", "Radnorshire"),
        ("Swansea", "Swansea"),
        ("Wrexham", "Wrexham"),
        # Scotland
        ("Aberdeen City", "Aberdeen City"),
        ("Aberdeenshire", "Aberdeenshire"),
        ("Angus", "Angus"),
        ("Argyll and Bute", "Argyll and Bute"),
        ("Clackmannanshire", "Clackmannanshire"),
        ("Dumfries and Galloway", "Dumfries and Galloway"),
        ("Dundee City", "Dundee City"),
        ("East Ayrshire", "East Ayrshire"),
        ("East Dunbartonshire", "East Dunbartonshire"),
        ("East Lothian", "East Lothian"),
        ("East Renfrewshire", "East Renfrewshire"),
        ("Edinburgh", "Edinburgh"),
        ("Falkirk", "Falkirk"),
        ("Fife", "Fife"),
        ("Glasgow City", "Glasgow City"),
        ("Highland", "Highland"),
        ("Inverclyde", "Inverclyde"),
        ("Midlothian", "Midlothian"),
        ("Moray", "Moray"),
        ("North Ayrshire", "North Ayrshire"),
        ("North Lanarkshire", "North Lanarkshire"),
        ("Orkney Islands", "Orkney Islands"),
        ("Perth and Kinross", "Perth and Kinross"),
        ("Renfrewshire", "Renfrewshire"),
        ("Scottish Borders", "Scottish Borders"),
        ("Shetland Islands", "Shetland Islands"),
        ("South Ayrshire", "South Ayrshire"),
        ("South Lanarkshire", "South Lanarkshire"),
        ("Stirling", "Stirling"),
        ("West Dunbartonshire", "West Dunbartonshire"),
        ("West Lothian", "West Lothian"),
        ("Western Isles", "Western Isles"),
    )
    county = models.CharField(
        max_length=64,
        choices=UK_COUNTY_CHOICES,
        blank=True,
        null=True,
        help_text="County of residence"
    )
    """User profile model to extend the User model with additional fields."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(
        upload_to='mobility_mapper_business_portal/profile_photos/',
        blank=True,
        null=True,
    )
    is_wheeler = models.BooleanField(default=False)
    has_business = models.BooleanField(default=False)
    has_registered_business = models.BooleanField(
        default=False,
        help_text="Whether the user has registered their business on the site."
    )

    MOBILITY_DEVICE_CHOICES = (
        ('manual_wheelchair', 'Manual Wheelchair'),
        ('powered_wheelchair', 'Powered Wheelchair'),
        ('manual_wheelchair_with_powered_front_attachment',
            'Manual Wheelchair with Powered Front Attachment'),
        ('all_terrain_wheelchair', 'All Terrain Wheelchair'),
        ('mobility_scooter_class_2', 'Mobility Scooter Class 2 (for footpaths)'),
        ('mobility_scooter_class_3', 'Mobility Scooter Class 3 (for road use)'),
        ('tricycle', 'Tricycle'),
        ('handcycle', 'Handcycle'),
        ('adapted_bicycle', 'Adapted Bicycle'),
        ('bicycle', 'Bicycle'),
        ('other', 'Other'),
    )
    # Allow multiple mobility devices
    mobility_devices = models.JSONField(
        default=list,
        blank=True,
        help_text="Types of wheeled mobility devices (if user is a wheeler)."
    )
    mobility_devices_other = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Other mobility device description (if 'Other' selected)."
    )

    AGE_GROUP_CHOICES = (
        ("under_18", "Under 18"),
        ("18_24", "18-24"),
        ("25_34", "25-34"),
        ("35_44", "35-44"),
        ("45_54", "45-54"),
        ("55_64", "55-64"),
        ("65_plus", "65+"),
    )
    age_group = models.CharField(
        max_length=16,
        choices=AGE_GROUP_CHOICES,
        blank=True,
        null=True,
        help_text="User's age group."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

# Automatically create/update UserProfile when User is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Skip auto-creation when loading fixtures (raw=True)
    if kwargs.get('raw', False):
        return
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
