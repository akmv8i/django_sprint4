from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET', 'POST'])
def registration(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})