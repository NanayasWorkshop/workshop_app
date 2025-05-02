from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@login_required
def profile_view(request):
    """
    View for user to see and update their profile information
    """
    if request.method == 'POST':
        # Handle password change
        if 'password_change' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Update session to prevent logout
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('workshop_app:profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        # Handle profile info update
        else:
            # Get basic user info from form
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            
            # Update user
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            messages.success(request, 'Your profile has been updated!')
            return redirect('workshop_app:profile')
    else:
        password_form = PasswordChangeForm(request.user)
    
    # Check if user has an operator profile
    has_operator_profile = hasattr(request.user, 'operator')
    
    context = {
        'password_form': password_form,
        'has_operator_profile': has_operator_profile,
    }
    
    if has_operator_profile:
        context['operator'] = request.user.operator
    
    return render(request, 'registration/profile.html', context)
