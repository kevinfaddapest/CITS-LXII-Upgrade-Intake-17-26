from django import forms
from .models import Contribution, Case, Rank
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class BootstrapRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter email'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(BootstrapRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class BootstrapLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })

class ContributionForm(forms.ModelForm):
    class Meta:
        model = Contribution
        fields = ['rank', 'names', 'contribution', 'contact', 'case']
        widgets = {
            'rank': forms.Select(attrs={'class':'form-select'}),
            'names': forms.TextInput(attrs={'class':'form-control','placeholder':'Full Name'}),
            'contribution': forms.NumberInput(attrs={'class':'form-control','placeholder':'Contribution'}),
            'contact': forms.TextInput(attrs={'class':'form-control','placeholder':'Contact'}),
            'case': forms.Select(attrs={'class':'form-select'}),
        }

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['bereaved_member_name', 'relation']
        widgets = {
            'bereaved_member_name': forms.TextInput(attrs={'class': 'form-control'}),
            'relation': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'bereaved_member_name': 'Case Owner',      # Updated label
            'relation': 'Case Details',                 # Updated label
        }

class RankForm(forms.ModelForm):
    class Meta:
        model = Rank
        fields = ['rank_name']
        widgets = {
            'rank_name': forms.TextInput(attrs={'class':'form-control','placeholder':'Rank Name'}),
        }
