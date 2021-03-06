from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class ToasterUser(models.Model):
  user_id = models.AutoField(primary_key=True)
  user_name = models.CharField(max_length=64)
  real_name = models.CharField(max_length=64)
  email_address = models.CharField(max_length=64)
  passwd_hash = models.CharField(max_length=64)
  active = models.BooleanField()
  admin = models.BooleanField()

  class Meta:
        db_table = u'users'
        
  def __str__(self):
    return "%s's ToasterUser " % (self.userprofile.user)

class Telescope(models.Model):
  telescope_id = models.AutoField(primary_key=True)
  telescope_name = models.CharField(null=False, max_length=64)
  latitude = models.DecimalField()
  longitude = models.DecimalField()
  datum = models.CharField(max_length=64)
  itrf_x = models.DecimalField(null=False)
  itrf_y = models.DecimalField(null=False)
  itrf_z = models.DecimalField(null=False)
  telescope_abbrev= models.CharField(null=False, max_length=16)
  telescope_code = models.CharField(null=False, max_length=2)
  class Meta:
        db_table = u'telescopes'  

class UserProfile(models.Model):
  user = models.ForeignKey(User)
  toaster_user = models.ForeignKey(ToasterUser)
  oauth_token = models.CharField(max_length=128)
  oauth_token_secret = models.CharField(max_length=128)
  def __str__(self):
    return "%s's profile. oauth_token: %s oauth_token_secret: %s " % ( self.user , self.oauth_token, self.oauth_token_secret )

def create_user_profile(sender, instance, created, **kwargs):
	if created:
		profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
