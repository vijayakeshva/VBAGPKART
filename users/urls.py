from django.urls import path
from users.views import user_register_view, user_login_view, user_logout_view

urlpatterns = [
    path("register/", user_register_view),
    path("login/", user_login_view),
    path("logout/", user_logout_view)
]
