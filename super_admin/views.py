from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from users.models import User, PlatformUser
from functions.general_functions.decorators import allow_access_by_role


@allow_access_by_role(
    user_type=User.UserType.PLATFORM,
    allowed_roles=[PlatformUser.Role.SUPER_ADMIN]
)
def super_admin_dashboard_view(request):
    return render(request, "dashboard/dashboard.html")

def super_admin_profile_view(request):
    return render(request, "dashboard/profile.html")

def super_admin_password_change_view(request):
    return render(request, "dashboard/users/password_change.html")

def super_admin_user_list_view(request):
    users = User.objects.all()
    return render(request, "dashboard/users/user_list.html", {'users': users})

def super_admin_user_detail_view(request, pk):
    user = get_object_or_404(User, id=pk)
    return render(request, "dashboard/users/user_detail.html", {'user': user})

def super_admin_user_create_view(request):
    return render(request, "dashboard/users/user_create.html")

def super_admin_user_update_view(request, pk):
    # user = User.objects.get(id=pk)
    user = get_object_or_404(User, id=pk)
    if request.method=="POST":
        data = request.POST
        username = data.get("uname")

        user.username=username
        # user.profile.mobile=mobile
        user.save()

    return render(request, "dashboard/users/user_update.html", {'user': user})
def super_admin_user_delete_view(request, pk):
    return redirect(".")

def super_admin_user_activate_view(request, pk):
    user = get_object_or_404(User, id=pk)
    user.is_active=True
    user.save()
    return redirect("/super_admin/user-list/")

def super_admin_user_dactivate_view(request, pk):
    user = get_object_or_404(User, id=pk)
    user.is_active=False
    user.save()
    return redirect("/super_admin/user-list/")
