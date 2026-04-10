from django import forms
from .models import Booking


class InternalBookingForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    department = forms.CharField(max_length=100)
    reason     = forms.CharField(widget=forms.Textarea)

    class Meta:
        model  = Booking
        fields = ['start_time', 'end_time']

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get('start_time'), cleaned.get('end_time')
        if s and e and e <= s:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned


class ExternalBookingStep1Form(forms.Form):
    full_name = forms.CharField(max_length=150, label='Full Name')
    phone     = forms.CharField(max_length=20,  label='Phone Number')
    email     = forms.EmailField(label='Email Address')
    reason    = forms.CharField(widget=forms.Textarea, label='Reason for Booking')


class ExternalBookingStep3Form(forms.Form):
    card_name   = forms.CharField(max_length=100, label='Name on Card')
    card_number = forms.CharField(max_length=19,  label='Card Number')
    expiry      = forms.CharField(max_length=5,   label='Expiry (MM/YY)')
    cvv         = forms.CharField(max_length=3,   label='CVV', widget=forms.PasswordInput)

    def clean_card_number(self):
        num = self.cleaned_data['card_number'].replace(' ', '')
        if len(num) < 16:
            raise forms.ValidationError('Enter a valid 16-digit card number.')
        return num

    def clean_expiry(self):
        exp = self.cleaned_data['expiry']
        if len(exp) < 5:
            raise forms.ValidationError('Enter expiry as MM/YY.')
        return exp

    def clean_cvv(self):
        cvv = self.cleaned_data['cvv']
        if len(cvv) < 3:
            raise forms.ValidationError('Enter a valid 3-digit CVV.')
        return cvv
