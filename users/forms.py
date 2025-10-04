from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    """
    Форма регистрации пользователя
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите отдел'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
        
        # Убираем помощь по паролю
        for field_name in ['password1', 'password2']:
            self.fields[field_name].help_text = None
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.department = self.cleaned_data['department']
        
        if commit:
            user.save()
        return user
