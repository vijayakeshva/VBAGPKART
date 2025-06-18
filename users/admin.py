from django.contrib import admin
from users.models import User, PlatformUser, BuyerUser

admin.site.register((User,PlatformUser, BuyerUser))
