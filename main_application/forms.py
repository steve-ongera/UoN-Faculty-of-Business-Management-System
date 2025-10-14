from django import forms
from .models import Student, User

class UserProfileForm(forms.ModelForm):
    """Form for editing user-related profile information"""
    
    class Meta:
        model = User
        fields = ['email', 'phone_number', 'profile_picture']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., +254712345678'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'profile_picture': 'Profile Picture'
        }
        help_texts = {
            'profile_picture': 'Upload a clear photo (JPG, PNG). Max 2MB.'
        }
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError('Image file too large ( > 2MB )')
        return picture


class StudentProfileForm(forms.ModelForm):
    """Form for editing student-specific profile information"""
    
    class Meta:
        model = Student
        fields = [
            'phone', 'email', 'date_of_birth', 'address',
            'parent_name', 'parent_phone',
            'guardian_name', 'guardian_phone'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your contact number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email address'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your physical address'
            }),
            'parent_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent/Guardian full name'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent contact number'
            }),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian full name (if different)'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian contact number'
            })
        }
        labels = {
            'phone': 'Personal Phone Number',
            'email': 'Personal Email',
            'date_of_birth': 'Date of Birth',
            'address': 'Current Address',
            'parent_name': 'Parent Name',
            'parent_phone': 'Parent Phone Number',
            'guardian_name': 'Guardian Name',
            'guardian_phone': 'Guardian Phone Number'
        }