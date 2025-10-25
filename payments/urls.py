"""
URL configuration for payments app
"""

from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    # Payment intent management
    path("create-intent/", views.CreatePaymentIntentView.as_view(), name="create-intent"),
    path("intent/<int:payment_intent_id>/", views.PaymentIntentDetailView.as_view(), name="payment-intent-detail"),
    
    # Khalti payment verification
    path("khalti/verify/", views.KhaltiVerificationView.as_view(), name="khalti-verify"),
    path("khalti/webhook/", views.KhaltiWebhookView.as_view(), name="khalti-webhook"),
    
    # QR code generation
    path("qr-code/<uuid:payment_intent_id>/", views.QRCodeView.as_view(), name="qr-code"),
]
