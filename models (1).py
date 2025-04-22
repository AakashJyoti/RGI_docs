from django.db import models

# Create your models here.

class GarageMaster(models.Model):
    GarageID = models.IntegerField()
    City_or_Village_ID_PK = models.IntegerField(null=True, blank=True)
    DIstrictID = models.IntegerField(null=True, blank=True)
    State_ID_PK = models.IntegerField(null=True, blank=True)
    GarageName = models.CharField(max_length=100)
    Address = models.CharField(max_length=250)
    PinCode = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.GarageName


class UserDetails(models.Model):
    session_id = models.UUIDField(max_length=100, null=True, blank=True)
    call_sid = models.CharField(max_length=100, null=True, blank=True)
    selected_language = models.CharField(max_length=100, null=True, blank=True)
    policy_number = models.CharField(max_length=50, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    transfer_reason = models.CharField(max_length=255, null=True, blank=True)
    covernote_number = models.CharField(max_length=50, null=True, blank=True)
    insured_name = models.CharField(max_length=255, null=True, blank=True)
    policy_start_date = models.CharField(max_length=255, null=True, blank=True)
    policy_end_date = models.CharField(max_length=255, null=True, blank=True)
    EngineNo = models.CharField(max_length=50, null=True, blank=True)
    ChassisNo = models.CharField(max_length=50, null=True, blank=True)
    VehiclNo = models.CharField(max_length=20, null=True, blank=True)
    CONTACTNO_MOBILE = models.CharField(max_length=15, null=True, blank=True)
    EmailID = models.CharField(max_length=255, null=True, blank=True)
    FirstName = models.CharField(max_length=100, null=True, blank=True)
    LastName = models.CharField(max_length=100, null=True, blank=True)
    Address = models.CharField(max_length=255, null=True, blank=True)
    CityName = models.CharField(max_length=100, null=True, blank=True)
    DistrictName = models.CharField(max_length=100, null=True, blank=True)
    StateName = models.CharField(max_length=100, null=True, blank=True)
    Pinno = models.CharField(max_length=10, null=True, blank=True)
    DOB = models.CharField(max_length=255, null=True, blank=True)
    Gender = models.CharField(max_length=10, null=True, blank=True)
    StateID = models.CharField(max_length=255, null=True, blank=True)
    DistrictID = models.CharField(max_length=255, null=True, blank=True)
    CityID = models.CharField(max_length=255, null=True, blank=True)
    Endt_no = models.CharField(max_length=50, null=True, blank=True)
    PRODUCT_CODE = models.CharField(max_length=50, null=True, blank=True)
    is_insured = models.BooleanField(default=False)
    relationship = models.CharField(max_length=50, null=True, blank=True)
    caller_name = models.CharField(max_length=100, null=True, blank=True)
    caller_mobile = models.CharField(max_length=15, null=True, blank=True)
    claim_type = models.CharField(max_length=50, null=True, blank=True)
    accident_date = models.CharField(max_length=255, null=True, blank=True)
    HourOfLoss = models.CharField(max_length=255, null=True, blank=True)
    MinOfLoss = models.CharField(max_length=255, null=True, blank=True)
    accident_location = models.CharField(max_length=255, null=True, blank=True)
    driver_info = models.CharField(max_length=255, null=True, blank=True)
    accident_info = models.CharField(max_length=255, null=True, blank=True)
    claim_no = models.CharField(max_length=50, null=True, blank=True)
    GarageID = models.CharField(max_length=255, null=True, blank=True)
    GarageName = models.CharField(max_length=255, null=True, blank=True)
    Garage_Address = models.CharField(max_length=255, null=True, blank=True)
    Garage_Pincode = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.FirstName} {self.LastName} ({self.policy_number})"