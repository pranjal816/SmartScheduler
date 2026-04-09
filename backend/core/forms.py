from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Batch, Classroom, Subject, Teacher, TimeSlot


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter teacher name"}
            )
        }


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "capacity"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Room 101"}
            ),
            "capacity": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Seating capacity"}
            ),
        }


class SubjectForm(forms.ModelForm):
    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = Subject
        fields = ["name", "lectures_per_week", "teachers", "is_lab"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Mathematics"}
            ),
            "lectures_per_week": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_lab": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ["day", "start_time", "end_time", "is_lunch"]
        widgets = {
            "day": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "is_lunch": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["name", "year", "subjects"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., CS-A"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g., 1"}),
            "subjects": forms.CheckboxSelectMultiple(),
        }
