from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Booking


class BookingForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Any special requests or setup requirements… (optional)',
        }),
        label='Notes',
    )

    class Meta:
        model = Booking
        fields = ['start_time', 'end_time', 'notes']

    def __init__(self, *args, **kwargs):
        # Accept an optional 'resource' kwarg for overlap checking at form level
        self.resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if start and end:
            # Basic chronology check
            if end <= start:
                raise forms.ValidationError('End time must be after start time.')

            # Start time must not be in the past
            if start < timezone.now():
                raise forms.ValidationError('Start time cannot be in the past.')

        return cleaned_data
