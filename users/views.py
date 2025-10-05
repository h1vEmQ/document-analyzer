from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import DetailView, CreateView
from django.urls import reverse_lazy
from .models import User
from .forms import UserRegisterForm


class CustomLoginView(LoginView):
    """
    Кастомное представление для входа в систему
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('documents:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Проверяем настройки Microsoft AD SSO
        try:
            from settings.models import ApplicationSettings
            settings_obj = ApplicationSettings.get_settings()
            
            context['microsoft_ad_enabled'] = settings_obj.microsoft_ad_sso_enabled
            context['microsoft_ad_domain'] = settings_obj.microsoft_ad_sso_domain
        except Exception:
            context['microsoft_ad_enabled'] = False
            context['microsoft_ad_domain'] = None
        
        return context


class CustomLogoutView(LogoutView):
    """
    Кастомное представление для выхода из системы
    """
    template_name = 'registration/logged_out.html'
    next_page = reverse_lazy('users:login')


class UserProfileView(LoginRequiredMixin, DetailView):
    """
    Профиль пользователя
    """
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class UserRegisterView(CreateView):
    """
    Регистрация нового пользователя
    """
    model = User
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('documents:list')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Регистрация прошла успешно!')
        return redirect(self.success_url)