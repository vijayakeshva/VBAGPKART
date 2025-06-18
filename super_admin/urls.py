from django.urls import path
from super_admin.views import (super_admin_dashboard_view,
                               super_admin_profile_view,
                               super_admin_password_change_view,
                               super_admin_user_list_view,
                               super_admin_user_detail_view,
                               super_admin_user_create_view,
                               super_admin_user_update_view,
                               super_admin_user_delete_view,
                               super_admin_user_activate_view,
                               super_admin_user_dactivate_view,
)

urlpatterns = [
    path("dashboard/", super_admin_dashboard_view),
    path("profile/", super_admin_profile_view),
    path("password-change/", super_admin_password_change_view),
    path("user-list/", super_admin_user_list_view),
    path("user-detail/<int:pk>/", super_admin_user_detail_view),
    path("user-create/", super_admin_user_create_view),
    path("user-update/<int:pk>/", super_admin_user_update_view),
    path("user-delete/<int:pk>/", super_admin_user_delete_view),
    path("user-activate/<int:pk>/", super_admin_user_activate_view),
    path("user-dactivate/<int:pk>/", super_admin_user_dactivate_view),
]

