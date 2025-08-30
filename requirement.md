# Charity Management System – Backend Requirements

## Functional Requirements

### 1. Authentication & Security
- JWT-based authentication for secure API access.
- Role-based access control (Donor, Admin).
- Password hashing (using Django's default PBKDF2 or bcrypt).
- Input validation and CSRF protection for sensitive endpoints.

### 2. Database Models
- **User**
  - id, username, email, password, role (donor/admin), created_at.
- **CharityCase**
  - id, title, description, category (cancer, accident, acid attack, education),
    documents, target_amount, collected_amount, verification_status, urgency_flag, created_at.
- **Donation**
  - id, donor_id, case_id, amount, payment_reference, timestamp.
- **RecommendationHistory**
  - id, user_id, case_id, score, timestamp.

### 3. REST APIs
- **Auth APIs**
  - POST `/api/auth/register` – User registration.
  - POST `/api/auth/login` – User login with JWT.
  - POST `/api/auth/logout` – Invalidate token.

- **Donor APIs**
  - GET `/api/cases/` – List charity cases with filters.
  - GET `/api/cases/{id}/` – Get case details.
  - POST `/api/donate/` – Make a donation.
  - GET `/api/donations/` – Get donor’s donation history.

- **Admin APIs**
  - POST `/api/cases/` – Add new case.
  - PUT `/api/cases/{id}/approve/` – Approve case.
  - PUT `/api/cases/{id}/reject/` – Reject case.
  - GET `/api/reports/` – View donation and category-wise reports.

- **Recommendation API**
  - GET `/api/recommendations/` – Suggest cases to a donor.

- **Search & Filter API**
  - GET `/api/cases/search?q={keyword}&category={category}`

### 4. Payment Integration
- QR-code-based payment gateway (eSewa, Khalti API).
- Store transaction reference securely in Donation table.

### 5. Notifications
- Email confirmation after successful donation.
- Periodic updates to donors about case progress.

### 6. Admin Tools
- Dashboard analytics: total donations, number of donors, active cases.
- Export donation records as CSV/Excel.

---

## Algorithms

### 1. Rule-Based Filtering
- Assigns priority levels (High/Medium/Low) to charity cases based on urgency, verification, and completeness of documents.

### 2. Donation Recommendation
- **Content-Based Filtering**  
  - Matches donor’s previous donation categories with new cases.
- **K-Means Clustering (ML)**  
  - Clusters donors based on donation patterns (amount, frequency, categories).  
  - Recommendations are made based on the cluster a donor belongs to.
- **Decision Tree (Classification)**  
  - Predicts which category of case a donor is most likely to support.  
  - Features: donor’s past donations, frequency, demographic info.  

### 3. Search & Filter
- Keyword search on title and description.
- Category and location-based filtering.
- **TF-IDF (Information Retrieval)**  
  - Improves keyword search ranking by prioritizing relevant cases.

### 4. Fraud/Spam Detection
- **Naïve Bayes Classifier**  
  - Classifies charity cases as genuine or potentially fraudulent.  
  - Features: completeness of documents, donor verification, donation patterns.

### 5. Donation Trend Analysis
- **Apriori Algorithm (Association Rule Mining)**  
  - Finds frequent donation patterns.  
  - Example: donors who donate to *Education* also often donate to *Medical* cases.  
  - Used for cross-category recommendations.

### 6. Time-Series Forecasting (Optional)
- **ARIMA / Moving Average**  
  - Predicts future donation amounts and trends.  
  - Helps admins in fundraising planning and resource allocation.

---

## Non-Functional Requirements
- **Performance**: APIs should respond within 500ms for typical queries.
- **Scalability**: Database schema supports large number of cases and donations.
- **Security**: HTTPS, JWT, password hashing, secure API endpoints.
- **Maintainability**: Modular Django apps (users, cases, donations, payments).
- **Reliability**: Error handling with proper HTTP status codes.

---

## Tech Stack (Backend)
- **Framework**: Django + Django REST Framework (DRF)
- **Database**: PostgreSQL or MySQL
- **Authentication**: JWT (SimpleJWT package)
- **ML/Algorithms**:  
  - Scikit-learn (K-Means, Decision Tree, Naïve Bayes, Apriori)  
  - NLTK/Scikit-learn TF-IDF (for search improvement)  
  - Statsmodels (for ARIMA forecasting, optional)
- **Payment Integration**: eSewa/Khalti API with QR code support
- **Task Scheduling**: Celery + Redis (for periodic notifications)
- **Deployment**: Docker + Nginx + Gunicorn
- **Version Control**: Git + GitHub
