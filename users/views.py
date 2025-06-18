from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import User
from django.contrib.auth import authenticate, login, logout

def user_register_view(request):
    return render(request, "users/user_register.html")  

def user_login_view(request):
    if request.method=="POST":
        data = request.POST
        usern = data.get("uname")
        pswd = data.get("psw")
        user = authenticate(request, username=usern, password=pswd)
        if user is not None:
            login(request, user)
    return render(request, "users/user_login.html")

def user_logout_view(request):
    logout(request)
    return redirect("/users/login/")