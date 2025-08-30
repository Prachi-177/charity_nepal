"""
URL configuration for payments app
"""

from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    # Payment intent management
    path(
        "create-intent/", views.CreatePaymentIntentView.as_view(), name="create-intent"
    ),
    path(
        "intent/<int:payment_intent_id>/",
        views.PaymentIntentDetailView.as_view(),
        name="payment-intent-detail",
    ),
    # Payment verification endpoints
    path("esewa/verify/", views.EsewaVerificationView.as_view(), name="esewa-verify"),
    path(
        "khalti/verify/", views.KhaltiVerificationView.as_view(), name="khalti-verify"
    ),
    # Webhook endpoints for payment gateways
    path("esewa/callback/", views.EsewaCallbackView.as_view(), name="esewa-callback"),
    path("khalti/webhook/", views.KhaltiWebhookView.as_view(), name="khalti-webhook"),
    # QR code generation
    path(
        "qr-code/<int:payment_intent_id>/", views.QRCodeView.as_view(), name="qr-code"
    ),
    # Payment history and analytics
    path("transactions/", views.TransactionHistoryView.as_view(), name="transactions"),
    path("analytics/", views.PaymentAnalyticsView.as_view(), name="analytics"),
]
