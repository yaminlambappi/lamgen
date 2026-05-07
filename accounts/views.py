from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, RegistrationForm


def _is_safe_redirect_url(url: str) -> bool:
    """Return True only if url is a relative same-origin path."""
    if not url:
        return False
    # Reject absolute URLs (contain scheme or start with //)
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return False
    # Must start with / to be a valid path
    if not url.startswith('/'):
        return False
    # Reject protocol-relative URLs
    if url.startswith('//'):
        return False
    return True


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Rotate session ID to prevent session fixation attacks (Req 1.3)
                request.session.cycle_key()
                # Merge any session bookmarks into DB bookmarks
                try:
                    from tools.utils.bookmarks import merge_session_bookmarks
                    merge_session_bookmarks(request, user)
                except Exception:
                    pass
                # Validate next parameter to prevent open redirect attacks (Req 1.4)
                next_url = request.POST.get('next') or request.GET.get('next', '')
                if _is_safe_redirect_url(next_url):
                    return redirect(next_url)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out.')
    return redirect('home')
