import requests
import bcrypt
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

# Supabase Configuration
SUPABASE_URL = 'https://mdgcgvvghvjofjtbpxcb.supabase.co'
SUPABASE_API_KEY = 'YOUR-API-KEY'

HEADERS = {
    'apikey': SUPABASE_API_KEY,
    'Authorization': f'Bearer {SUPABASE_API_KEY}',
    'Content-Type': 'application/json'
}

def dashboard_redirect(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')

    role = user.get('role')
    if role == 'admin':
        return redirect('dashboard_admin')
    return redirect('dashboard_user')

# Register
class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('full_name')
        role = request.POST.get('role')

        if not all([email, password, name, role]):
            messages.error(request, "Semua field harus diisi.")
            return render(request, 'accounts/register.html')

        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        data = {
            "email": email,
            "password": hashed_pw,
            "full_name": name,
            "role": role
        }

        res = requests.post(f'{SUPABASE_URL}/rest/v1/users', headers=HEADERS, json=data)
        if res.status_code == 201:
            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')
        messages.error(request, "Gagal registrasi. Email mungkin sudah digunakan.")
        return render(request, 'accounts/register.html')

# Login
class LoginView(View):
    def get(self, request):
        next_url = request.GET.get('next', '')
        return render(request, 'accounts/login.html', {'next': next_url})

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')

        if not email or not password:
            messages.error(request, "Email dan password harus diisi.")
            return render(request, 'accounts/login.html', {'next': next_url})

        res = requests.get(f'{SUPABASE_URL}/rest/v1/users?email=eq.{email}', headers=HEADERS)
        user_data = res.json()

        if user_data and bcrypt.checkpw(password.encode(), user_data[0]['password'].encode()):
            request.session['user'] = user_data[0]
            messages.success(request, f"Selamat datang, {user_data[0]['full_name']}!")
            
            if next_url:
                return redirect(next_url)
            return redirect('dashboard_redirect')

        messages.error(request, "Email atau password salah.")
        return render(request, 'accounts/login.html', {'next': next_url})


# Dashboard
class DashboardView(View):
    def get(self, request):
        user = request.session.get('user')
        if not user:
            messages.warning(request, "Silakan login terlebih dahulu.")
            return redirect('login')
        return render(request, 'dashboard.html', {'user': user})

# Logout
class LogoutView(View):
    def get(self, request):
        request.session.flush()
        messages.success(request, "Berhasil logout.")
        return redirect('login')



def dashboard_user(request):
    user = request.session.get('user')
    if not user:
        return redirect('login')
    return render(request, 'dashboard_user.html', {'user': user})


def dashboard_admin(request):
    user = request.session.get('user')
    if not user or user.get('role') != 'admin':
        return redirect('login')
    return render(request, 'dashboard_admin.html', {'user': user})
