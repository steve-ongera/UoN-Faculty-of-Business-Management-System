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

from django import forms
from .models import GradingScheme, Programme

class GradingSchemeForm(forms.ModelForm):
    """Form for creating and updating grading schemes"""
    
    class Meta:
        model = GradingScheme
        fields = [
            'programme',
            'grade',
            'min_marks',
            'max_marks',
            'grade_point',
            'description'
        ]
        
        widgets = {
            'programme': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A, B+, C',
                'required': True,
                'maxlength': '5'
            }),
            'min_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'required': True
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100.00',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'required': True
            }),
            'grade_point': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '4.00',
                'step': '0.01',
                'min': '0',
                'max': '5',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Distinction, Pass, Fail',
                'required': True,
                'maxlength': '50'
            })
        }
        
        labels = {
            'programme': 'Programme',
            'grade': 'Grade',
            'min_marks': 'Minimum Marks (%)',
            'max_marks': 'Maximum Marks (%)',
            'grade_point': 'Grade Point',
            'description': 'Description'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active programmes
        self.fields['programme'].queryset = Programme.objects.filter(
            is_active=True
        ).select_related('department').order_by('code')
        
        # Add help text
        self.fields['grade'].help_text = 'Enter the grade letter (e.g., A, B, C)'
        self.fields['min_marks'].help_text = 'Minimum marks to achieve this grade'
        self.fields['max_marks'].help_text = 'Maximum marks for this grade'
        self.fields['grade_point'].help_text = 'Grade point value for GPA calculation'
        self.fields['description'].help_text = 'Description (e.g., Distinction, Pass, Fail)'
    
    def clean(self):
        cleaned_data = super().clean()
        min_marks = cleaned_data.get('min_marks')
        max_marks = cleaned_data.get('max_marks')
        
        if min_marks is not None and max_marks is not None:
            if min_marks >= max_marks:
                raise forms.ValidationError(
                    "Minimum marks must be less than maximum marks."
                )
            
            if min_marks < 0 or max_marks > 100:
                raise forms.ValidationError(
                    "Marks must be between 0 and 100."
                )
        
        return cleaned_data