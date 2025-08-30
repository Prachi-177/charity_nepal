from django import forms
from django.core.exceptions import ValidationError

from .models import Donation


class DonationForm(forms.ModelForm):
    """Form for creating donations"""

    class Meta:
        model = Donation
        fields = [
            "amount",
            "donor_message",
            "is_anonymous",
            "donor_name",
            "donor_email",
            "payment_method",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Enter amount (Rs.)",
                    "min": "50",
                    "step": "1",
                }
            ),
            "donor_message": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full",
                    "placeholder": "Leave an encouraging message (optional)",
                    "rows": 3,
                }
            ),
            "is_anonymous": forms.CheckboxInput(
                attrs={"class": "checkbox checkbox-success"}
            ),
            "donor_name": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "Your full name",
                }
            ),
            "donor_email": forms.EmailInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": "your.email@example.com",
                }
            ),
            "payment_method": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # If user is authenticated, pre-populate and hide some fields
        if user and user.is_authenticated:
            self.fields["donor_name"].initial = user.get_full_name() or user.username
            self.fields["donor_email"].initial = user.email
            self.fields["donor_name"].widget.attrs["readonly"] = True
            self.fields["donor_email"].widget.attrs["readonly"] = True

        # Set field labels
        self.fields["amount"].label = "Donation Amount (NPR)"
        self.fields["donor_message"].label = "Message of Support"
        self.fields["is_anonymous"].label = "Make this donation anonymous"
        self.fields["donor_name"].label = "Full Name"
        self.fields["donor_email"].label = "Email Address"
        self.fields["payment_method"].label = "Payment Method"

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount < 50:
            raise ValidationError("Minimum donation amount is Rs. 50")
        if amount and amount > 1000000:
            raise ValidationError("Maximum donation amount is Rs. 10,00,000")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get("is_anonymous")
        donor_name = cleaned_data.get("donor_name")
        donor_email = cleaned_data.get("donor_email")

        # If not anonymous, require name and email
        if not is_anonymous:
            if not donor_name:
                self.add_error(
                    "donor_name", "Name is required for non-anonymous donations"
                )
            if not donor_email:
                self.add_error(
                    "donor_email", "Email is required for non-anonymous donations"
                )

        return cleaned_data
