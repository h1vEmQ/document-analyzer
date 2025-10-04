from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class AdminUserCreateForm(UserCreationForm):
    """
    Форма создания пользователя администратором
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email адрес'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    is_staff = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка полей пароля
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
        
        # Установка лейблов
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email адрес'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['role'].label = 'Роль'
        self.fields['is_active'].label = 'Активный пользователь'
        self.fields['is_staff'].label = 'Доступ к админ-панели Django'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
    
    def clean_email(self):
        """Проверяем уникальность email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def save(self, commit=True):
        """Сохраняем пользователя с установкой роли"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.is_active = self.cleaned_data['is_active']
        user.is_staff = self.cleaned_data['is_staff']
        
        if commit:
            user.save()
        return user


class AdminUserEditForm(forms.ModelForm):
    """
    Форма редактирования пользователя администратором
    """
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль (оставьте пустым для сохранения текущего)'
        }),
        help_text='Оставьте поле пустым, чтобы сохранить текущий пароль'
    )
    
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите email адрес'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Установка лейблов
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email адрес'
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['role'].label = 'Роль'
        self.fields['is_active'].label = 'Активный пользователь'
        self.fields['is_staff'].label = 'Доступ к админ-панели Django'
        self.fields['is_superuser'].label = 'Суперпользователь'
        self.fields['new_password'].label = 'Новый пароль'
        self.fields['confirm_password'].label = 'Подтверждение пароля'
        
        # Настройка выбора роли
        self.fields['role'].choices = User.ROLE_CHOICES
    
    def clean_email(self):
        """Проверяем уникальность email"""
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk:
            # При редактировании исключаем текущего пользователя
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Пользователь с таким email уже существует.')
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def clean(self):
        """Проверяем совпадение паролей"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('Пароли не совпадают.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Сохраняем пользователя с обновлением пароля при необходимости"""
        user = super().save(commit=False)
        
        # Обновляем пароль, если указан новый
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()
        return user
