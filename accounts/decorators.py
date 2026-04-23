from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(role):
    """
    Decorator for views that checks whether a user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.role != role:
                messages.error(request, f"Access denied. Only {role}s can access this page.")
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
