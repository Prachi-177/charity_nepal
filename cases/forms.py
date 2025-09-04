from django import forms
from django.core.exceptions import ValidationError

from .models import CharityCase


class CharityCaseForm(forms.ModelForm):
    """Form for creating and updating charity cases"""

    class Meta:
        model = CharityCase
        fields = [
            "title",
            "description",
            "category",
            "target_amount",
            "urgency_flag",
            "location",
            "beneficiary_name",
            "beneficiary_age",
            "contact_phone",
            "contact_email",
            "featured_image",
            "documents",
            "deadline",
            "tags",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Enter a compelling campaign title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full h-32",
                    "placeholder": "Tell the story of your campaign. Be detailed and specific about the need and how funds will be used.",
                }
            ),
            "category": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "target_amount": forms.NumberInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "0.00",
                    "min": "100",
                    "step": "0.01",
                }
            ),
            "urgency_flag": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "City, District, Nepal",
                }
            ),
            "beneficiary_name": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Full name of the beneficiary",
                }
            ),
            "beneficiary_age": forms.NumberInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Age",
                    "min": "1",
                    "max": "120",
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "+977-XXXXXXXXX",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "contact@example.com",
                }
            ),
            "featured_image": forms.FileInput(
                attrs={
                    "class": "file-input file-input-bordered w-full",
                    "accept": "image/*",
                }
            ),
            "documents": forms.FileInput(
                attrs={
                    "class": "file-input file-input-bordered w-full",
                    "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png",
                }
            ),
            "deadline": forms.DateTimeInput(
                attrs={"class": "input input-bordered w-full", "type": "datetime-local"}
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "medical, urgent, surgery (comma-separated)",
                }
            ),
        }

    def clean_target_amount(self):
        target_amount = self.cleaned_data.get("target_amount")
        if target_amount and target_amount < 100:
            raise ValidationError("Target amount must be at least Rs. 100.")
        return target_amount

    def clean_contact_phone(self):
        phone = self.cleaned_data.get("contact_phone")
        if phone and not phone.startswith("+977"):
            raise ValidationError("Phone number must start with +977.")
        return phone


class CaseSearchForm(forms.Form):
    """Search form for charity cases"""

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Search campaigns by title, description, or beneficiary name",
            }
        ),
    )

    category = forms.ChoiceField(
        choices=[("", "All Categories")] + CharityCase.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    urgency = forms.ChoiceField(
        choices=[("", "All Urgency Levels")] + CharityCase.URGENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
