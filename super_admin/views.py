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
    user_type = User.UserType.choices
    gender = User.Gender.choices
    role = PlatformUser.Role.choices

    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        phone_number = data.get("phone_number")
        user_type_val = data.get("user_type")
        gender_val = data.get("gender")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        role_val = data.get("role")
        deportment = data.get("deportment")
        employee_id = data.get("employee_id")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("/super_admin/user-create/")

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            user_type=user_type_val,
            gender=gender_val,
            password=password
        )

        PlatformUser.objects.create(
            user=user,
            role=role_val,
            department=deportment,
            employee_id=employee_id
        )

        messages.success(request, "User created successfully.")
        return redirect("/super_admin/user-list/")

    return render(request, "dashboard/users/user_create.html", {
        'user_type': user_type,
        'gender': gender,
        'role': role
    })
def super_admin_user_update_view(request,pk):
    user = get_object_or_404(User, id=pk)

    try:
        platform_user = user.platform_user  
    except PlatformUser.DoesNotExist:
        platform_user = None

    if request.method == "POST":
        user.email = request.POST.get("email")
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.phone_number = request.POST.get("phone_number")
        user.gender = request.POST.get("gender")

        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password and password == confirm_password:
            user.set_password(password)

        user.save()

    
        if platform_user:
            platform_user.role = request.POST.get("role")
            platform_user.department = request.POST.get("department")
            platform_user.employee_id = request.POST.get("employee_id")
            platform_user.save()

       # messages.success(request, "User updated successfully!")

    return render(request, "dashboard/users/user_update.html", {
        "user": user,
        "role": PlatformUser.Role.choices,
    })


def super_admin_user_delete_view(request, pk):
    user =User.objects.get(id=pk)
    user.delete()
    return redirect("/super_admin/user-list/")

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
