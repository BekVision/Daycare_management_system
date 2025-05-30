from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, UserProfile, Role


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2", "role")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "role")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'address', 'birth_date',
            'shift_start', 'shift_end', 'photo'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'shift_start': forms.TimeInput(attrs={'type': 'time'}),
            'shift_end': forms.TimeInput(attrs={'type': 'time'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Foydalanuvchi nomi'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )