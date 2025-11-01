# 🚀 CHARITY NEPAL BACKEND - COMPLETE API DOCUMENTATION

## 📋 **TABLE OF CONTENTS**

1. [Base Configuration](#base-configuration)
2. [Authentication APIs](#authentication-apis)
3. [User Management APIs](#user-management-apis)
4. [Charity Cases APIs](#charity-cases-apis)
5. [Donations APIs](#donations-apis)
6. [Payments APIs](#payments-apis)
7. [Recommendations APIs](#recommendations-apis)
8. [System Health APIs](#system-health-apis)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## 🔧 **BASE CONFIGURATION**

### **Base URL**

```
Development: http://127.0.0.1:8000
Production: https://your-domain.com
```

### **API Base Path**

All API endpoints are prefixed with `/api/`

### **Authentication**

- **Type**: JWT Bearer Token
- **Header**: `Authorization: Bearer <your_jwt_token>`
- **Token Expiry**: Access tokens expire in 60 minutes, Refresh tokens in 7 days

### **Content Type**

- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

### **HTTP Status Codes**

```
200 OK - Success
201 Created - Resource created successfully
400 Bad Request - Invalid request data
401 Unauthorized - Authentication required
403 Forbidden - Permission denied
404 Not Found - Resource not found
429 Too Many Requests - Rate limit exceeded
500 Internal Server Error - Server error
```

---

## 🔐 **AUTHENTICATION APIs**

### **1. User Registration**

```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+977-9841234567",
    "address": "Kathmandu, Nepal",
    "role": "donor"  // Options: "donor", "admin"
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "donor",
      "phone": "+977-9841234567",
      "address": "Kathmandu, Nepal",
      "is_verified": false,
      "created_at": "2025-08-29T10:30:00Z"
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

### **2. User Login**

```http
POST /api/auth/login/
Content-Type: application/json

{
    "email": "john@example.com",
    "password": "SecurePass123!"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "donor",
      "is_verified": true
    },
    "tokens": {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

### **3. User Logout**

```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Logout successful"
}
```

### **4. Token Refresh**

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## 👤 **USER MANAGEMENT APIs**

### **1. Get User Profile**

```http
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "donor",
  "phone": "+977-9841234567",
  "address": "Kathmandu, Nepal",
  "is_verified": true,
  "created_at": "2025-08-29T10:30:00Z",
  "updated_at": "2025-08-29T10:30:00Z"
}
```

### **2. Update User Profile**

```http
PATCH /api/auth/profile/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "first_name": "John Updated",
    "phone": "+977-9841234568",
    "address": "Pokhara, Nepal"
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John Updated",
  "last_name": "Doe",
  "role": "donor",
  "phone": "+977-9841234568",
  "address": "Pokhara, Nepal",
  "is_verified": true,
  "updated_at": "2025-08-29T11:00:00Z"
}
```

### **3. Change Password**

```http
POST /api/auth/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

### **4. Password Reset Request**

```http
POST /api/auth/password-reset/
Content-Type: application/json

{
    "email": "john@example.com"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

### **5. Email Verification**

```http
POST /api/auth/verify-email/
Content-Type: application/json

{
    "token": "verification_token_here"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Email verified successfully"
}
```

---

## 📋 **CHARITY CASES APIs**

### **1. List All Cases**

```http
GET /api/cases/
Authorization: Bearer <access_token> (optional for public cases)

# Query Parameters:
# ?category=cancer
# ?status=approved
# ?urgency=high
# ?search=cancer treatment
# ?ordering=-created_at
# ?page=1
# ?page_size=10
```

**Response (200 OK):**

```json
{
  "count": 25,
  "next": "http://127.0.0.1:8000/api/cases/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Help Save Lives: Cancer Treatment Fund",
      "description": "Urgent support needed for cancer treatment...",
      "category": "cancer",
      "target_amount": "500000.00",
      "collected_amount": "125000.00",
      "completion_percentage": 25,
      "verification_status": "approved",
      "urgency_flag": "high",
      "location": "Kathmandu",
      "beneficiary_name": "Ram Bahadur",
      "beneficiary_age": 45,
      "contact_phone": "+977-9841234567",
      "contact_email": "contact@example.com",
      "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg",
      "created_by": {
        "id": 1,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe"
      },
      "created_at": "2025-08-29T10:30:00Z",
      "updated_at": "2025-08-29T10:30:00Z",
      "deadline": "2025-12-31T23:59:59Z",
      "slug": "help-save-lives-cancer-treatment-fund",
      "tags": "cancer,medical,urgent"
    }
  ]
}
```

### **2. Get Case Details**

```http
GET /api/cases/{id}/
Authorization: Bearer <access_token> (optional for approved cases)
```

**Response (200 OK):**

```json
{
  "id": 1,
  "title": "Help Save Lives: Cancer Treatment Fund",
  "description": "Detailed description of the case...",
  "category": "cancer",
  "target_amount": "500000.00",
  "collected_amount": "125000.00",
  "completion_percentage": 25,
  "verification_status": "approved",
  "urgency_flag": "high",
  "location": "Kathmandu",
  "beneficiary_name": "Ram Bahadur",
  "beneficiary_age": 45,
  "contact_phone": "+977-9841234567",
  "contact_email": "contact@example.com",
  "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg",
  "documents": "http://127.0.0.1:8000/media/cases/documents/medical_report.pdf",
  "created_by": {
    "id": 1,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe"
  },
  "approved_by": {
    "id": 2,
    "username": "admin",
    "first_name": "Admin",
    "last_name": "User"
  },
  "created_at": "2025-08-29T10:30:00Z",
  "updated_at": "2025-08-29T10:30:00Z",
  "deadline": "2025-12-31T23:59:59Z",
  "slug": "help-save-lives-cancer-treatment-fund",
  "tags": "cancer,medical,urgent",
  "updates": [
    {
      "id": 1,
      "title": "Treatment Started",
      "content": "Patient has started chemotherapy...",
      "created_at": "2025-08-30T10:00:00Z"
    }
  ],
  "donation_count": 15,
  "recent_donations": [
    {
      "amount": "5000.00",
      "donor_name": "Anonymous",
      "created_at": "2025-08-29T15:30:00Z"
    }
  ]
}
```

### **3. Create New Case**

```http
POST /api/cases/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
    "title": "Help Save Lives: Cancer Treatment Fund",
    "description": "Detailed description of the case...",
    "category": "cancer",
    "target_amount": "500000.00",
    "urgency_flag": "high",
    "location": "Kathmandu",
    "beneficiary_name": "Ram Bahadur",
    "beneficiary_age": 45,
    "contact_phone": "+977-9841234567",
    "contact_email": "contact@example.com",
    "deadline": "2025-12-31T23:59:59Z",
    "tags": "cancer,medical,urgent",
    "featured_image": [file],
    "documents": [file]
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "title": "Help Save Lives: Cancer Treatment Fund",
  "description": "Detailed description of the case...",
  "category": "cancer",
  "target_amount": "500000.00",
  "collected_amount": "0.00",
  "completion_percentage": 0,
  "verification_status": "pending",
  "urgency_flag": "high",
  "location": "Kathmandu",
  "beneficiary_name": "Ram Bahadur",
  "beneficiary_age": 45,
  "contact_phone": "+977-9841234567",
  "contact_email": "contact@example.com",
  "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg",
  "documents": "http://127.0.0.1:8000/media/cases/documents/medical_report.pdf",
  "created_by": {
    "id": 1,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe"
  },
  "created_at": "2025-08-29T10:30:00Z",
  "updated_at": "2025-08-29T10:30:00Z",
  "deadline": "2025-12-31T23:59:59Z",
  "slug": "help-save-lives-cancer-treatment-fund",
  "tags": "cancer,medical,urgent"
}
```

### **4. Update Case**

```http
PATCH /api/cases/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Updated Title",
    "description": "Updated description...",
    "urgency_flag": "critical"
}
```

### **5. Delete Case**

```http
DELETE /api/cases/{id}/
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

### **6. Search Cases**

```http
GET /api/cases/search/
Authorization: Bearer <access_token> (optional)

# Query Parameters:
# ?q=cancer treatment
# ?category=medical
# ?location=kathmandu
# ?min_amount=10000
# ?max_amount=500000
```

**Response (200 OK):**

```json
{
  "results": [
    {
      "id": 1,
      "title": "Help Save Lives: Cancer Treatment Fund",
      "description": "Brief description...",
      "category": "cancer",
      "target_amount": "500000.00",
      "collected_amount": "125000.00",
      "completion_percentage": 25,
      "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg",
      "urgency_flag": "high",
      "location": "Kathmandu"
    }
  ],
  "count": 1
}
```

### **7. Get Case Categories**

```http
GET /api/cases/categories/
```

**Response (200 OK):**

```json
{
  "categories": [
    {
      "key": "cancer",
      "label": "Cancer Treatment",
      "count": 15
    },
    {
      "key": "accident",
      "label": "Accident Support",
      "count": 8
    },
    {
      "key": "education",
      "label": "Education Support",
      "count": 12
    }
  ]
}
```

### **8. Get Case Statistics**

```http
GET /api/cases/stats/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "total_cases": 50,
  "approved_cases": 35,
  "pending_cases": 10,
  "rejected_cases": 3,
  "completed_cases": 2,
  "total_target_amount": "5000000.00",
  "total_collected_amount": "2500000.00",
  "average_completion_rate": 65.5,
  "category_breakdown": {
    "cancer": 15,
    "accident": 8,
    "education": 12,
    "medical": 10,
    "disaster": 5
  }
}
```

### **9. Get Featured Cases**

```http
GET /api/cases/featured/
```

**Response (200 OK):**

```json
{
  "featured_cases": [
    {
      "id": 1,
      "title": "Help Save Lives: Cancer Treatment Fund",
      "description": "Brief description...",
      "target_amount": "500000.00",
      "collected_amount": "125000.00",
      "completion_percentage": 25,
      "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg",
      "urgency_flag": "high"
    }
  ]
}
```

---

## 💰 **DONATIONS APIs**

### **1. List User Donations**

```http
GET /api/donations/
Authorization: Bearer <access_token>

# Query Parameters:
# ?case_id=1
# ?status=completed
# ?ordering=-created_at
# ?page=1
```

**Response (200 OK):**

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "case": {
        "id": 1,
        "title": "Help Save Lives: Cancer Treatment Fund",
        "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg"
      },
      "donor": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe"
      },
      "amount": "5000.00",
      "is_anonymous": false,
      "payment_method": " ",
      "status": "completed",
      "message": "Hope this helps!",
      "created_at": "2025-08-29T15:30:00Z",
      "payment_confirmed_at": "2025-08-29T15:35:00Z",
      "transaction_id": "TXN123456789"
    }
  ]
}
```

### **2. Create Donation**

```http
POST /api/donations/create/
Authorization: Bearer <access_token> (optional for anonymous donations)
Content-Type: application/json

{
    "case_id": 1,
    "amount": "5000.00",
    "is_anonymous": false,
    "payment_method": " ",
    "message": "Hope this helps with the treatment!",
    "donor_name": "John Doe",  // Required if anonymous
    "donor_email": "john@example.com"  // Required if anonymous
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "case": {
    "id": 1,
    "title": "Help Save Lives: Cancer Treatment Fund"
  },
  "donor": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe"
  },
  "amount": "5000.00",
  "is_anonymous": false,
  "payment_method": " ",
  "status": "pending",
  "message": "Hope this helps with the treatment!",
  "created_at": "2025-08-29T15:30:00Z",
  "payment_intent": {
    "id": 1,
    "amount": "5000.00",
    "gateway": " ",
    "payment_url": "https:// .com.np/payment?pid=1&amt=5000"
  }
}
```

### **3. Get Donation Details**

```http
GET /api/donations/{id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": 1,
  "case": {
    "id": 1,
    "title": "Help Save Lives: Cancer Treatment Fund",
    "featured_image": "http://127.0.0.1:8000/media/cases/images/case1.jpg"
  },
  "donor": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe"
  },
  "amount": "5000.00",
  "is_anonymous": false,
  "payment_method": " ",
  "status": "completed",
  "message": "Hope this helps with the treatment!",
  "created_at": "2025-08-29T15:30:00Z",
  "payment_confirmed_at": "2025-08-29T15:35:00Z",
  "transaction_id": "TXN123456789",
  "receipt_url": "http://127.0.0.1:8000/api/donations/1/receipt/"
}
```

### **4. Get Donation History**

```http
GET /api/donations/history/
Authorization: Bearer <access_token>

# Query Parameters:
# ?year=2025
# ?month=8
# ?case_category=cancer
```

**Response (200 OK):**

```json
{
  "total_donations": 25,
  "total_amount": "125000.00",
  "average_donation": "5000.00",
  "donations_by_month": [
    {
      "month": "2025-08",
      "count": 10,
      "total_amount": "50000.00"
    }
  ],
  "donations_by_category": [
    {
      "category": "cancer",
      "count": 8,
      "total_amount": "40000.00"
    }
  ],
  "recent_donations": [
    {
      "id": 1,
      "case_title": "Help Save Lives: Cancer Treatment Fund",
      "amount": "5000.00",
      "created_at": "2025-08-29T15:30:00Z",
      "status": "completed"
    }
  ]
}
```

### **5. Get Donation Statistics**

```http
GET /api/donations/stats/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "total_donations": 500,
  "total_amount": "5000000.00",
  "average_donation": "10000.00",
  "completed_donations": 450,
  "pending_donations": 40,
  "failed_donations": 10,
  "top_donors": [
    {
      "donor_name": "John Doe",
      "total_amount": "50000.00",
      "donation_count": 10
    }
  ],
  "donation_trends": {
    "this_month": "500000.00",
    "last_month": "450000.00",
    "growth_rate": 11.1
  }
}
```

### **6. Get Recent Donations (Public)**

```http
GET /api/donations/recent/
```

**Response (200 OK):**

```json
{
  "recent_donations": [
    {
      "case_title": "Help Save Lives: Cancer Treatment Fund",
      "donor_name": "Anonymous",
      "amount": "5000.00",
      "created_at": "2025-08-29T15:30:00Z",
      "message": "Hope this helps!"
    }
  ]
}
```

### **7. Get Donation Leaderboard**

```http
GET /api/donations/leaderboard/
```

**Response (200 OK):**

```json
{
  "top_donors": [
    {
      "rank": 1,
      "donor_name": "John Doe",
      "total_amount": "100000.00",
      "donation_count": 20,
      "is_anonymous": false
    }
  ],
  "top_cases": [
    {
      "rank": 1,
      "case_title": "Help Save Lives: Cancer Treatment Fund",
      "total_raised": "500000.00",
      "donation_count": 50,
      "target_amount": "750000.00"
    }
  ]
}
```

---

## 💳 **PAYMENTS APIs**

### **1. Create Payment Intent**

```http
POST /api/payments/create-intent/
Authorization: Bearer <access_token> (optional)
Content-Type: application/json

{
    "donation_id": 1,
    "gateway": " ",  // Options: " ", "khalti"
    "return_url": "https://yourapp.com/payment/success",
    "cancel_url": "https://yourapp.com/payment/cancel"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "donation": {
    "id": 1,
    "amount": "5000.00",
    "case_title": "Help Save Lives: Cancer Treatment Fund"
  },
  "gateway": " ",
  "amount": "5000.00",
  "currency": "NPR",
  "status": "pending",
  "payment_url": "https:// .com.np/payment?pid=1&amt=5000&scd=CHARITY&su=https://yourapp.com/success&fu=https://yourapp.com/failure",
  "qr_code_url": "http://127.0.0.1:8000/api/payments/qr-code/1/",
  "created_at": "2025-08-29T15:30:00Z",
  "expires_at": "2025-08-29T16:30:00Z"
}
```

### **2. Get Payment Intent Details**

```http
GET /api/payments/intent/{payment_intent_id}/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "id": 1,
  "donation": {
    "id": 1,
    "amount": "5000.00",
    "case_title": "Help Save Lives: Cancer Treatment Fund"
  },
  "gateway": " ",
  "amount": "5000.00",
  "currency": "NPR",
  "status": "completed",
  "payment_url": "https:// .com.np/payment?pid=1&amt=5000",
  "transaction_id": "TXN123456789",
  "created_at": "2025-08-29T15:30:00Z",
  "completed_at": "2025-08-29T15:35:00Z",
  "expires_at": "2025-08-29T16:30:00Z"
}
```

### **3. Verify   Payment**

```http
POST /api/payments/ /verify/
Content-Type: application/json

{
    "payment_intent_id": 1,
    "oid": "payment_order_id",
    "amt": "5000.00",
    "refId": " _reference_id"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Payment verified successfully",
  "data": {
    "payment_intent_id": 1,
    "transaction_id": "TXN123456789",
    "amount": "5000.00",
    "status": "completed",
    "verified_at": "2025-08-29T15:35:00Z"
  }
}
```

### **4. Verify Khalti Payment**

```http
POST /api/payments/khalti/verify/
Content-Type: application/json

{
    "payment_intent_id": 1,
    "token": "khalti_payment_token",
    "amount": 500000  // Amount in paisa (NPR * 100)
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Payment verified successfully",
  "data": {
    "payment_intent_id": 1,
    "transaction_id": "TXN123456789",
    "amount": "5000.00",
    "status": "completed",
    "verified_at": "2025-08-29T15:35:00Z"
  }
}
```

### **5. Get QR Code for Payment**

```http
GET /api/payments/qr-code/{payment_intent_id}/
```

**Response (200 OK):**

```
Content-Type: image/png
[QR Code Image Binary Data]
```

### **6. Get Transaction History**

```http
GET /api/payments/transactions/
Authorization: Bearer <access_token>

# Query Parameters:
# ?gateway= 
# ?status=completed
# ?start_date=2025-08-01
# ?end_date=2025-08-31
```

**Response (200 OK):**

```json
{
  "count": 25,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "donation": {
        "id": 1,
        "case_title": "Help Save Lives: Cancer Treatment Fund",
        "amount": "5000.00"
      },
      "gateway": " ",
      "amount": "5000.00",
      "status": "completed",
      "transaction_id": "TXN123456789",
      "created_at": "2025-08-29T15:30:00Z",
      "completed_at": "2025-08-29T15:35:00Z"
    }
  ]
}
```

### **7. Get Payment Analytics**

```http
GET /api/payments/analytics/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "total_transactions": 500,
  "total_amount": "5000000.00",
  "successful_transactions": 450,
  "failed_transactions": 40,
  "pending_transactions": 10,
  "success_rate": 90.0,
  "gateway_breakdown": {
    " ": {
      "count": 300,
      "amount": "3000000.00",
      "success_rate": 92.0
    },
    "khalti": {
      "count": 200,
      "amount": "2000000.00",
      "success_rate": 88.0
    }
  },
  "monthly_trends": [
    {
      "month": "2025-08",
      "transaction_count": 100,
      "total_amount": "1000000.00",
      "success_rate": 91.0
    }
  ]
}
```

---

## 🤖 **RECOMMENDATIONS APIs**

### **1. Get Personalized Recommendations**

```http
GET /api/recommendations/personal/
Authorization: Bearer <access_token>

# Query Parameters:
# ?limit=10
# ?algorithm=hybrid  // Options: hybrid, content_based, collaborative, clustering
```

**Response (200 OK):**

```json
{
  "recommendations": [
    {
      "case": {
        "id": 5,
        "title": "Emergency Surgery Fund",
        "description": "Brief description...",
        "category": "medical",
        "target_amount": "300000.00",
        "collected_amount": "75000.00",
        "completion_percentage": 25,
        "featured_image": "http://127.0.0.1:8000/media/cases/images/case5.jpg",
        "urgency_flag": "high"
      },
      "score": 0.95,
      "reason": "Based on your previous donations to medical cases",
      "algorithm": "content_based"
    }
  ],
  "algorithm_performance": {
    "hybrid": {
      "precision": 0.85,
      "recall": 0.78,
      "f1_score": 0.81
    }
  },
  "user_profile": {
    "preferred_categories": ["medical", "education"],
    "average_donation": "7500.00",
    "donation_frequency": "monthly"
  }
}
```

### **2. Get Trending Cases**

```http
GET /api/recommendations/trending/
```

**Response (200 OK):**

```json
{
  "trending_cases": [
    {
      "id": 3,
      "title": "Flood Relief Emergency Fund",
      "description": "Urgent support needed for flood victims...",
      "category": "disaster",
      "target_amount": "1000000.00",
      "collected_amount": "450000.00",
      "completion_percentage": 45,
      "featured_image": "http://127.0.0.1:8000/media/cases/images/case3.jpg",
      "urgency_flag": "critical",
      "trending_score": 0.92,
      "recent_donations_count": 25,
      "donation_velocity": 15.5 // donations per day
    }
  ],
  "trending_categories": [
    {
      "category": "disaster",
      "case_count": 5,
      "trending_score": 0.88
    }
  ]
}
```

### **3. Get User Preference Profile**

```http
GET /api/recommendations/profile/
Authorization: Bearer <access_token>
```

**Response (200 OK):**

```json
{
  "user_profile": {
    "id": 1,
    "user": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe"
    },
    "preferred_categories": ["medical", "education", "cancer"],
    "preferred_amount_range": {
      "min": "1000.00",
      "max": "10000.00"
    },
    "preferred_urgency": ["high", "critical"],
    "location_preference": "kathmandu",
    "interests": ["healthcare", "children", "emergency"],
    "donation_history": {
      "total_donations": 15,
      "total_amount": "75000.00",
      "average_donation": "5000.00",
      "favorite_category": "medical"
    },
    "recommendation_settings": {
      "enable_email_notifications": true,
      "frequency": "weekly",
      "max_recommendations": 10
    },
    "created_at": "2025-08-29T10:30:00Z",
    "updated_at": "2025-08-29T15:00:00Z"
  }
}
```

### **4. Update User Preference Profile**

```http
PATCH /api/recommendations/profile/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "preferred_categories": ["medical", "education"],
    "preferred_amount_range": {
        "min": "2000.00",
        "max": "15000.00"
    },
    "preferred_urgency": ["high"],
    "location_preference": "pokhara",
    "interests": ["healthcare", "education"],
    "recommendation_settings": {
        "enable_email_notifications": false,
        "frequency": "daily",
        "max_recommendations": 5
    }
}
```

### **5. Get Recommendation History**

```http
GET /api/recommendations/history/
Authorization: Bearer <access_token>

# Query Parameters:
# ?algorithm=hybrid
# ?action=clicked
# ?page=1
```

**Response (200 OK):**

```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "case": {
        "id": 5,
        "title": "Emergency Surgery Fund"
      },
      "algorithm": "hybrid",
      "score": 0.95,
      "action": "clicked",
      "recommended_at": "2025-08-29T10:30:00Z",
      "interacted_at": "2025-08-29T10:35:00Z"
    }
  ],
  "analytics": {
    "total_recommendations": 100,
    "clicked_recommendations": 35,
    "donated_from_recommendations": 8,
    "click_through_rate": 0.35,
    "conversion_rate": 0.23
  }
}
```

### **6. Track Recommendation Interaction**

```http
POST /api/recommendations/track/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "case_id": 5,
    "action": "clicked",  // Options: "viewed", "clicked", "donated", "shared"
    "algorithm": "hybrid",
    "score": 0.95,
    "position": 1,  // Position in recommendation list
    "session_id": "session_123"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Interaction tracked successfully",
  "data": {
    "recommendation_history_id": 1,
    "case_id": 5,
    "action": "clicked",
    "tracked_at": "2025-08-29T15:30:00Z"
  }
}
```

---

## 🏥 **SYSTEM HEALTH APIs**

### **1. Health Check**

```http
GET /api/health/
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2025-08-29T15:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "response_time": "15ms"
    },
    "redis": {
      "status": "healthy",
      "response_time": "5ms"
    },
    "celery": {
      "status": "healthy",
      "active_tasks": 2,
      "processed_tasks": 150
    },
    "storage": {
      "status": "healthy",
      "available_space": "85%"
    }
  },
  "statistics": {
    "total_users": 500,
    "total_cases": 150,
    "total_donations": 2500,
    "system_uptime": "15 days, 6 hours"
  }
}
```

### **2. Readiness Check**

```http
GET /api/ready/
```

**Response (200 OK):**

```json
{
  "status": "ready",
  "timestamp": "2025-08-29T15:30:00Z",
  "checks": {
    "database_connection": true,
    "redis_connection": true,
    "migrations_applied": true,
    "static_files_collected": true
  }
}
```

### **3. Liveness Check**

```http
GET /api/live/
```

**Response (200 OK):**

```json
{
  "status": "alive",
  "timestamp": "2025-08-29T15:30:00Z",
  "uptime": "15 days, 6 hours, 45 minutes"
}
```

---

## ❌ **ERROR HANDLING**

### **Error Response Format**

All API errors follow this consistent format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["This field is required."],
      "amount": ["Ensure this value is greater than or equal to 100."]
    }
  },
  "timestamp": "2025-08-29T15:30:00Z"
}
```

### **Common Error Codes**

| Code                      | HTTP Status | Description                     |
| ------------------------- | ----------- | ------------------------------- |
| `VALIDATION_ERROR`        | 400         | Invalid request data            |
| `AUTHENTICATION_REQUIRED` | 401         | Authentication required         |
| `INVALID_CREDENTIALS`     | 401         | Invalid login credentials       |
| `PERMISSION_DENIED`       | 403         | Insufficient permissions        |
| `NOT_FOUND`               | 404         | Resource not found              |
| `RATE_LIMIT_EXCEEDED`     | 429         | Too many requests               |
| `PAYMENT_FAILED`          | 400         | Payment processing failed       |
| `CASE_NOT_APPROVED`       | 400         | Case not approved for donations |
| `INSUFFICIENT_FUNDS`      | 400         | Payment amount insufficient     |
| `EXPIRED_TOKEN`           | 401         | JWT token has expired           |
| `INVALID_TOKEN`           | 401         | Invalid JWT token               |
| `SERVER_ERROR`            | 500         | Internal server error           |

### **Field Validation Errors**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Enter a valid email address."],
      "password": ["This password is too common."],
      "amount": ["Ensure this value is greater than or equal to 100."],
      "phone": ["Phone number must be in format: +977-XXXXXXXXX"]
    }
  }
}
```

---

## 🔒 **RATE LIMITING**

### **Rate Limits**

| Endpoint Category  | Authenticated Users | Anonymous Users    |
| ------------------ | ------------------- | ------------------ |
| Authentication     | 5 requests/minute   | 5 requests/minute  |
| Profile Management | 10 requests/minute  | N/A                |
| Cases (Read)       | 100 requests/minute | 20 requests/minute |
| Cases (Write)      | 10 requests/minute  | N/A                |
| Donations          | 20 requests/minute  | 5 requests/minute  |
| Payments           | 10 requests/minute  | 5 requests/minute  |
| Recommendations    | 50 requests/minute  | 10 requests/minute |
| Health Checks      | 20 requests/minute  | 20 requests/minute |

### **Rate Limit Headers**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1693310400
```

### **Rate Limit Exceeded Response**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2025-08-29T16:00:00Z"
    }
  }
}
```

---

## 📝 **DATA MODELS**

### **User Model**

```json
{
  "id": "integer",
  "username": "string (unique)",
  "email": "string (unique)",
  "first_name": "string",
  "last_name": "string",
  "role": "string (donor|admin)",
  "phone": "string (optional)",
  "address": "string (optional)",
  "is_verified": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### **Charity Case Model**

```json
{
  "id": "integer",
  "title": "string (max 200)",
  "description": "text",
  "category": "string (cancer|accident|education|medical|disaster|other)",
  "target_amount": "decimal",
  "collected_amount": "decimal",
  "completion_percentage": "integer (computed)",
  "verification_status": "string (pending|approved|rejected|completed|cancelled)",
  "urgency_flag": "string (low|medium|high|critical)",
  "location": "string (optional)",
  "beneficiary_name": "string",
  "beneficiary_age": "integer (optional)",
  "contact_phone": "string",
  "contact_email": "string",
  "featured_image": "url (optional)",
  "documents": "url (optional)",
  "created_by": "User object",
  "approved_by": "User object (optional)",
  "created_at": "datetime",
  "updated_at": "datetime",
  "deadline": "datetime (optional)",
  "slug": "string (unique)",
  "tags": "string (comma-separated)"
}
```

### **Donation Model**

```json
{
  "id": "integer",
  "case": "CharityCase object",
  "donor": "User object (optional for anonymous)",
  "amount": "decimal",
  "is_anonymous": "boolean",
  "payment_method": "string ( |khalti|bank_transfer)",
  "status": "string (pending|completed|failed|cancelled)",
  "message": "text (optional)",
  "donor_name": "string (for anonymous donations)",
  "donor_email": "string (for anonymous donations)",
  "created_at": "datetime",
  "payment_confirmed_at": "datetime (optional)",
  "transaction_id": "string (optional)"
}
```

### **Payment Intent Model**

```json
{
  "id": "integer",
  "donation": "Donation object",
  "gateway": "string ( |khalti)",
  "amount": "decimal",
  "currency": "string (NPR)",
  "status": "string (pending|completed|failed|expired)",
  "payment_url": "url",
  "transaction_id": "string (optional)",
  "gateway_response": "json (optional)",
  "created_at": "datetime",
  "completed_at": "datetime (optional)",
  "expires_at": "datetime"
}
```

---

## 🔄 **WEBHOOKS**

### **  Callback**

```http
POST /api/payments/ /callback/
Content-Type: application/x-www-form-urlencoded

oid=payment_order_id&
amt=5000.00&
refId= _reference_id&
pid=charity_product_id
```

### **Khalti Webhook**

```http
POST /api/payments/khalti/webhook/
Content-Type: application/json
Authorization: Bearer <khalti_webhook_secret>

{
    "event": "payment.success",
    "data": {
        "token": "khalti_payment_token",
        "amount": 500000,
        "idx": "khalti_payment_id"
    }
}
```

---

## 🎯 **INTEGRATION EXAMPLES**

### **Frontend Authentication Flow**

```javascript
// 1. Login
const loginResponse = await fetch("/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "john@example.com",
    password: "SecurePass123!",
  }),
});

const loginData = await loginResponse.json();
const accessToken = loginData.data.tokens.access;
const refreshToken = loginData.data.tokens.refresh;

// Store tokens securely
localStorage.setItem("accessToken", accessToken);
localStorage.setItem("refreshToken", refreshToken);

// 2. Use token for authenticated requests
const casesResponse = await fetch("/api/cases/", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
});
```

### **Donation Flow**

```javascript
// 1. Create donation
const donationResponse = await fetch("/api/donations/create/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    case_id: 1,
    amount: "5000.00",
    payment_method: " ",
    message: "Hope this helps!",
  }),
});

const donationData = await donationResponse.json();
const donationId = donationData.id;

// 2. Create payment intent
const paymentResponse = await fetch("/api/payments/create-intent/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    donation_id: donationId,
    gateway: " ",
    return_url: "https://yourapp.com/payment/success",
    cancel_url: "https://yourapp.com/payment/cancel",
  }),
});

const paymentData = await paymentResponse.json();

// 3. Redirect to payment gateway
window.location.href = paymentData.payment_url;
```

---

## 📊 **PAGINATION**

All list endpoints support pagination with the following parameters:

### **Query Parameters**

- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 20, max: 100)

### **Response Format**

```json
{
    "count": 150,
    "next": "http://127.0.0.1:8000/api/cases/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## 🔍 **FILTERING & SEARCH**

### **Common Query Parameters**

- `search`: Text search across relevant fields
- `ordering`: Sort by field (prefix with `-` for descending)
- `category`: Filter by category
- `status`: Filter by status
- `created_after`: Filter by date created after
- `created_before`: Filter by date created before

### **Example**

```http
GET /api/cases/?search=cancer&category=medical&ordering=-created_at&page=1&page_size=10
```

---

This comprehensive API documentation covers all endpoints, request/response formats, error handling, and integration examples for the Charity Nepal Backend. Use this as a complete reference for building your frontend application!
