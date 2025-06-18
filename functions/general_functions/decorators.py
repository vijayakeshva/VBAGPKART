from django.http import Http404
from django.shortcuts import redirect
from users.models import User

def allow_access_by_role(user_type=None, allowed_roles=None, redirect_url=None):
    """
    Decorator to restrict access to views based on UserType and specific roles
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                if redirect_url:
                    return redirect(redirect_url)
                raise Http404("Authentication required.")

            if user_type is not None and user.user_type != user_type:
                if redirect_url:
                    return redirect(redirect_url)
                raise Http404(f"Access denied. User type '{user.user_type}' is not '{user_type}'.")

            if allowed_roles:
                if user.user_type == User.UserType.PLATFORM:
                    if not hasattr(user, 'platform_user') or not user.platform_user:
                        if redirect_url:
                            return redirect(redirect_url)
                        raise Http404("Access denied. Platform user profile missing.")
                    
                    if user.platform_user.role not in allowed_roles:
                        if redirect_url:
                            return redirect(redirect_url)
                        raise Http404(f"Access denied. Platform role '{user.platform_user.role}' not allowed.")
                else:
                    if redirect_url:
                        return redirect(redirect_url)
                    raise Http404(f"Access denied. Role check not applicable or failed for user type: {user.user_type}")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator