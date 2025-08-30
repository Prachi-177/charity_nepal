"""
ML Algorithms for Charity Case Recommendation System
Implements various recommendation algorithms as specified in requirements
"""

import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger(__name__)


class ContentBasedRecommender:
    """Content-Based Filtering for charity case recommendations"""

    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000, stop_words="english", lowercase=True, ngram_range=(1, 2)
        )
        self.case_features = None
        self.case_ids = []

    def fit(self, cases_data: pd.DataFrame):
        """
        Train the content-based model

        Args:
            cases_data: DataFrame with columns ['id', 'title', 'description', 'category', 'tags']
        """
        # Combine text features
        text_features = (
            cases_data["title"]
            + " "
            + cases_data["description"]
            + " "
            + cases_data["tags"].fillna("")
        )

        # Create TF-IDF matrix
        self.case_features = self.tfidf_vectorizer.fit_transform(text_features)
        self.case_ids = cases_data["id"].tolist()

        logger.info(f"Content-based model trained on {len(cases_data)} cases")

    def recommend(
        self, user_donation_history: List[int], n_recommendations: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Recommend cases based on user's donation history

        Args:
            user_donation_history: List of case IDs user has donated to
            n_recommendations: Number of recommendations to return

        Returns:
            List of (case_id, score) tuples
        """
        if not user_donation_history or self.case_features is None:
            return []

        # Get user profile based on donated cases
        user_case_indices = [
            self.case_ids.index(case_id)
            for case_id in user_donation_history
            if case_id in self.case_ids
        ]

        if not user_case_indices:
            return []

        # Average the TF-IDF vectors of donated cases to create user profile
        user_profile = np.mean(self.case_features[user_case_indices].toarray(), axis=0)

        # Calculate similarity with all cases
        similarities = cosine_similarity([user_profile], self.case_features.toarray())[
            0
        ]

        # Get top recommendations (excluding already donated cases)
        case_scores = list(zip(self.case_ids, similarities))
        case_scores = [
            (case_id, score)
            for case_id, score in case_scores
            if case_id not in user_donation_history
        ]
        case_scores.sort(key=lambda x: x[1], reverse=True)

        return case_scores[:n_recommendations]


class DonorClusteringRecommender:
    """K-Means Clustering for donor segmentation and recommendations"""

    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.scaler = StandardScaler()
        self.donor_features = None
        self.cluster_case_preferences = {}

    def prepare_donor_features(self, donor_data: pd.DataFrame) -> np.ndarray:
        """
        Prepare donor features for clustering

        Args:
            donor_data: DataFrame with donor information and donation patterns

        Returns:
            Scaled feature matrix
        """
        features = []

        # Numerical features
        numerical_cols = [
            "avg_donation_amount",
            "total_donations",
            "total_donated",
            "donation_frequency_days",
        ]
        for col in numerical_cols:
            if col in donor_data.columns:
                features.append(donor_data[col].fillna(0))

        # Category preferences (one-hot encoding)
        if "preferred_categories" in donor_data.columns:
            categories = [
                "cancer",
                "accident",
                "acid_attack",
                "education",
                "disaster",
                "medical",
            ]
            for category in categories:
                category_pref = donor_data["preferred_categories"].apply(
                    lambda x: 1 if isinstance(x, list) and category in x else 0
                )
                features.append(category_pref)

        # Age and income encoding
        if "age_range" in donor_data.columns:
            age_encoder = LabelEncoder()
            age_encoded = age_encoder.fit_transform(
                donor_data["age_range"].fillna("unknown")
            )
            features.append(pd.Series(age_encoded))

        if "income_range" in donor_data.columns:
            income_encoder = LabelEncoder()
            income_encoded = income_encoder.fit_transform(
                donor_data["income_range"].fillna("unknown")
            )
            features.append(pd.Series(income_encoded))

        feature_matrix = (
            np.column_stack(features)
            if features
            else np.array([]).reshape(len(donor_data), 0)
        )
        return self.scaler.fit_transform(feature_matrix)

    def fit(self, donor_data: pd.DataFrame, donation_data: pd.DataFrame):
        """
        Train the clustering model

        Args:
            donor_data: DataFrame with donor information
            donation_data: DataFrame with donation history
        """
        # Prepare features
        self.donor_features = self.prepare_donor_features(donor_data)

        if self.donor_features.shape[1] == 0:
            logger.warning("No features available for clustering")
            return

        # Fit clustering
        self.kmeans.fit(self.donor_features)

        # Analyze cluster preferences
        donor_data["cluster"] = self.kmeans.labels_

        for cluster_id in range(self.n_clusters):
            cluster_donors = donor_data[donor_data["cluster"] == cluster_id][
                "id"
            ].tolist()
            cluster_donations = donation_data[
                donation_data["donor_id"].isin(cluster_donors)
            ]

            # Find most popular categories in this cluster
            category_counts = (
                cluster_donations.groupby("case_category")
                .size()
                .sort_values(ascending=False)
            )
            self.cluster_case_preferences[cluster_id] = category_counts.to_dict()

        logger.info(f"Donor clustering model trained with {self.n_clusters} clusters")

    def predict_cluster(self, donor_features: np.ndarray) -> int:
        """Predict cluster for a donor"""
        return self.kmeans.predict([donor_features])[0]

    def recommend_by_cluster(
        self,
        donor_cluster: int,
        available_cases: pd.DataFrame,
        n_recommendations: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Recommend cases based on cluster preferences

        Args:
            donor_cluster: Cluster ID of the donor
            available_cases: DataFrame of available cases
            n_recommendations: Number of recommendations

        Returns:
            List of (case_id, score) tuples
        """
        if donor_cluster not in self.cluster_case_preferences:
            return []

        cluster_prefs = self.cluster_case_preferences[donor_cluster]

        # Score cases based on cluster preferences
        case_scores = []
        for _, case in available_cases.iterrows():
            score = cluster_prefs.get(case["category"], 0) / max(
                sum(cluster_prefs.values()), 1
            )
            case_scores.append((case["id"], score))

        case_scores.sort(key=lambda x: x[1], reverse=True)
        return case_scores[:n_recommendations]


class DecisionTreeRecommender:
    """Decision Tree for predicting donation likelihood"""

    def __init__(self):
        self.model = DecisionTreeClassifier(
            max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42
        )
        self.feature_names = []
        self.label_encoders = {}

    def prepare_features(
        self, donor_data: pd.DataFrame, case_data: pd.DataFrame
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for decision tree

        Returns:
            Feature matrix and feature names
        """
        features = []
        feature_names = []

        # Donor features
        donor_numerical = [
            "avg_donation_amount",
            "total_donations",
            "donation_frequency_days",
        ]
        for col in donor_numerical:
            if col in donor_data.columns:
                features.append(donor_data[col].fillna(0))
                feature_names.append(f"donor_{col}")

        # Case features
        case_numerical = ["target_amount", "collected_amount", "urgency_score"]
        for col in case_numerical:
            if col in case_data.columns:
                features.append(case_data[col].fillna(0))
                feature_names.append(f"case_{col}")

        # Categorical features
        categorical_features = [
            ("donor_age_range", donor_data.get("age_range")),
            ("donor_income_range", donor_data.get("income_range")),
            ("case_category", case_data.get("category")),
            ("case_urgency", case_data.get("urgency_flag")),
        ]

        for feature_name, feature_data in categorical_features:
            if feature_data is not None:
                if feature_name not in self.label_encoders:
                    self.label_encoders[feature_name] = LabelEncoder()

                encoded = self.label_encoders[feature_name].fit_transform(
                    feature_data.fillna("unknown")
                )
                features.append(pd.Series(encoded))
                feature_names.append(feature_name)

        feature_matrix = (
            np.column_stack(features)
            if features
            else np.array([]).reshape(len(donor_data), 0)
        )
        return feature_matrix, feature_names

    def fit(
        self, donor_data: pd.DataFrame, case_data: pd.DataFrame, labels: np.ndarray
    ):
        """
        Train the decision tree model

        Args:
            donor_data: Donor information
            case_data: Case information
            labels: Binary labels (1 if donated, 0 if not)
        """
        X, feature_names = self.prepare_features(donor_data, case_data)
        self.feature_names = feature_names

        if X.shape[1] == 0:
            logger.warning("No features available for decision tree")
            return

        self.model.fit(X, labels)
        logger.info(f"Decision tree model trained on {len(X)} samples")

    def predict_donation_likelihood(
        self, donor_features: pd.DataFrame, case_features: pd.DataFrame
    ) -> np.ndarray:
        """
        Predict likelihood of donation

        Returns:
            Array of donation probabilities
        """
        X, _ = self.prepare_features(donor_features, case_features)
        if X.shape[1] == 0:
            return np.array([])

        return self.model.predict_proba(X)[:, 1]  # Probability of class 1 (donation)


class FraudDetectionClassifier:
    """Naive Bayes classifier for fraud detection"""

    def __init__(self):
        self.model = MultinomialNB(alpha=1.0)
        self.feature_names = []

    def prepare_fraud_features(
        self, case_data: pd.DataFrame
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for fraud detection

        Returns:
            Feature matrix and feature names
        """
        features = []
        feature_names = []

        # Document completeness score
        if "documents" in case_data.columns:
            doc_completeness = case_data["documents"].apply(lambda x: 1 if x else 0)
            features.append(doc_completeness)
            feature_names.append("has_documents")

        # Contact information completeness
        contact_features = ["contact_phone", "contact_email", "beneficiary_name"]
        for feature in contact_features:
            if feature in case_data.columns:
                completeness = case_data[feature].apply(
                    lambda x: 1 if pd.notna(x) and str(x).strip() else 0
                )
                features.append(completeness)
                feature_names.append(f"{feature}_complete")

        # Target amount analysis (unusually high amounts might be suspicious)
        if "target_amount" in case_data.columns:
            amount_percentile = pd.qcut(
                case_data["target_amount"], q=10, labels=False, duplicates="drop"
            )
            features.append(amount_percentile)
            feature_names.append("amount_percentile")

        # Description length and quality
        if "description" in case_data.columns:
            desc_length = case_data["description"].apply(len)
            desc_length_percentile = pd.qcut(
                desc_length, q=5, labels=False, duplicates="drop"
            )
            features.append(desc_length_percentile)
            feature_names.append("description_length_percentile")

        # Category distribution (some categories might be more prone to fraud)
        if "category" in case_data.columns:
            category_encoder = LabelEncoder()
            category_encoded = category_encoder.fit_transform(case_data["category"])
            features.append(pd.Series(category_encoded))
            feature_names.append("category")

        feature_matrix = (
            np.column_stack(features)
            if features
            else np.array([]).reshape(len(case_data), 0)
        )
        return feature_matrix, feature_names

    def fit(self, case_data: pd.DataFrame, fraud_labels: np.ndarray):
        """
        Train the fraud detection model

        Args:
            case_data: Case information
            fraud_labels: Binary labels (1 if fraud, 0 if genuine)
        """
        X, feature_names = self.prepare_fraud_features(case_data)
        self.feature_names = feature_names

        if X.shape[1] == 0:
            logger.warning("No features available for fraud detection")
            return

        # Ensure non-negative features for Multinomial NB
        X = np.abs(X)

        self.model.fit(X, fraud_labels)
        logger.info(f"Fraud detection model trained on {len(X)} samples")

    def predict_fraud_probability(self, case_data: pd.DataFrame) -> np.ndarray:
        """
        Predict fraud probability for cases

        Returns:
            Array of fraud probabilities
        """
        X, _ = self.prepare_fraud_features(case_data)
        if X.shape[1] == 0:
            return np.array([])

        X = np.abs(X)
        return self.model.predict_proba(X)[:, 1]  # Probability of fraud


class AprioriRecommender:
    """Association Rule Mining for cross-category recommendations"""

    def __init__(self, min_support: float = 0.1, min_confidence: float = 0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.association_rules = {}

    def fit(self, donation_data: pd.DataFrame):
        """
        Find association rules between donation categories

        Args:
            donation_data: DataFrame with donor_id and case_category columns
        """
        # Create transaction data (donor -> list of categories they've donated to)
        transactions = (
            donation_data.groupby("donor_id")["case_category"].apply(list).tolist()
        )

        # Find frequent itemsets and association rules
        # Simplified implementation - in production, use mlxtend.frequent_patterns
        category_counts = {}
        category_pairs = {}

        # Count individual categories
        for transaction in transactions:
            for category in set(transaction):
                category_counts[category] = category_counts.get(category, 0) + 1

        # Count category pairs
        for transaction in transactions:
            categories = list(set(transaction))
            for i in range(len(categories)):
                for j in range(i + 1, len(categories)):
                    pair = tuple(sorted([categories[i], categories[j]]))
                    category_pairs[pair] = category_pairs.get(pair, 0) + 1

        # Calculate association rules
        total_transactions = len(transactions)

        for pair, pair_count in category_pairs.items():
            if pair_count / total_transactions >= self.min_support:
                cat1, cat2 = pair

                # Rule: cat1 -> cat2
                confidence_1_2 = pair_count / category_counts[cat1]
                if confidence_1_2 >= self.min_confidence:
                    if cat1 not in self.association_rules:
                        self.association_rules[cat1] = []
                    self.association_rules[cat1].append((cat2, confidence_1_2))

                # Rule: cat2 -> cat1
                confidence_2_1 = pair_count / category_counts[cat2]
                if confidence_2_1 >= self.min_confidence:
                    if cat2 not in self.association_rules:
                        self.association_rules[cat2] = []
                    self.association_rules[cat2].append((cat1, confidence_2_1))

        logger.info(f"Found {len(self.association_rules)} association rules")

    def recommend_categories(
        self, donated_categories: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Recommend categories based on association rules

        Args:
            donated_categories: List of categories user has donated to

        Returns:
            List of (category, confidence) tuples
        """
        recommendations = {}

        for category in donated_categories:
            if category in self.association_rules:
                for rec_category, confidence in self.association_rules[category]:
                    if rec_category not in donated_categories:
                        if rec_category not in recommendations:
                            recommendations[rec_category] = confidence
                        else:
                            recommendations[rec_category] = max(
                                recommendations[rec_category], confidence
                            )

        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)


class HybridRecommendationSystem:
    """Combines multiple recommendation algorithms"""

    def __init__(self):
        self.content_based = ContentBasedRecommender()
        self.clustering = DonorClusteringRecommender()
        self.decision_tree = DecisionTreeRecommender()
        self.fraud_detector = FraudDetectionClassifier()
        self.apriori = AprioriRecommender()

    def fit_all_models(
        self,
        donor_data: pd.DataFrame,
        case_data: pd.DataFrame,
        donation_data: pd.DataFrame,
    ):
        """
        Train all recommendation models
        """
        logger.info("Training hybrid recommendation system...")

        # Content-based filtering
        self.content_based.fit(case_data)

        # Clustering
        self.clustering.fit(donor_data, donation_data)

        # Decision tree (needs positive/negative examples)
        # This is a simplified example - in practice, you'd need to prepare proper training data

        # Fraud detection (needs labeled fraud data)
        # This would require manual labeling or rule-based initial labels

        # Association rules
        self.apriori.fit(donation_data)

        logger.info("All models trained successfully")

    def get_hybrid_recommendations(
        self,
        user_id: int,
        donor_data: pd.DataFrame,
        available_cases: pd.DataFrame,
        n_recommendations: int = 10,
    ) -> List[Dict]:
        """
        Get hybrid recommendations combining multiple algorithms

        Returns:
            List of recommendation dictionaries with scores from different algorithms
        """
        recommendations = {}

        # Get user's donation history
        from donations.models import Donation

        user_donations = Donation.objects.filter(donor_id=user_id, status="completed")
        donated_case_ids = list(user_donations.values_list("case_id", flat=True))
        donated_categories = list(
            user_donations.values_list("case__category", flat=True)
        )

        # Content-based recommendations
        content_recs = self.content_based.recommend(
            donated_case_ids, n_recommendations * 2
        )
        for case_id, score in content_recs:
            if case_id not in recommendations:
                recommendations[case_id] = {"case_id": case_id, "scores": {}}
            recommendations[case_id]["scores"]["content_based"] = score

        # Clustering-based recommendations
        user_data = donor_data[donor_data["id"] == user_id]
        if not user_data.empty:
            user_features = self.clustering.prepare_donor_features(user_data)
            if user_features.shape[1] > 0:
                user_cluster = self.clustering.predict_cluster(user_features[0])
                cluster_recs = self.clustering.recommend_by_cluster(
                    user_cluster, available_cases, n_recommendations * 2
                )
                for case_id, score in cluster_recs:
                    if case_id not in recommendations:
                        recommendations[case_id] = {"case_id": case_id, "scores": {}}
                    recommendations[case_id]["scores"]["clustering"] = score

        # Association rule recommendations
        category_recs = self.apriori.recommend_categories(donated_categories)
        for category, confidence in category_recs:
            category_cases = available_cases[available_cases["category"] == category]
            for _, case in category_cases.iterrows():
                case_id = case["id"]
                if case_id not in recommendations:
                    recommendations[case_id] = {"case_id": case_id, "scores": {}}
                recommendations[case_id]["scores"]["association"] = confidence

        # Calculate final hybrid score
        for case_id in recommendations:
            scores = recommendations[case_id]["scores"]
            # Weighted combination of different algorithms
            final_score = (
                scores.get("content_based", 0) * 0.4
                + scores.get("clustering", 0) * 0.3
                + scores.get("association", 0) * 0.3
            )
            recommendations[case_id]["final_score"] = final_score

        # Sort by final score and return top N
        sorted_recs = sorted(
            recommendations.values(), key=lambda x: x["final_score"], reverse=True
        )
        return sorted_recs[:n_recommendations]

    def save_models(self, filepath: str):
        """Save trained models to disk"""
        models = {
            "content_based": self.content_based,
            "clustering": self.clustering,
            "decision_tree": self.decision_tree,
            "fraud_detector": self.fraud_detector,
            "apriori": self.apriori,
        }

        with open(filepath, "wb") as f:
            pickle.dump(models, f)

        logger.info(f"Models saved to {filepath}")

    def load_models(self, filepath: str):
        """Load trained models from disk"""
        with open(filepath, "rb") as f:
            models = pickle.load(f)

        self.content_based = models["content_based"]
        self.clustering = models["clustering"]
        self.decision_tree = models["decision_tree"]
        self.fraud_detector = models["fraud_detector"]
        self.apriori = models["apriori"]

        logger.info(f"Models loaded from {filepath}")


# Utility functions for TF-IDF search improvement
class TFIDFSearchEnhancer:
    """TF-IDF based search ranking for charity cases"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            lowercase=True,
            ngram_range=(1, 3),
            token_pattern=r"(?u)\b\w\w+\b",
        )
        self.case_vectors = None
        self.case_ids = []

    def fit(self, cases: pd.DataFrame):
        """
        Fit TF-IDF vectorizer on case data

        Args:
            cases: DataFrame with case information
        """
        # Combine all text fields
        text_data = (
            cases["title"].fillna("")
            + " "
            + cases["description"].fillna("")
            + " "
            + cases["tags"].fillna("")
            + " "
            + cases["category"].fillna("")
        )

        self.case_vectors = self.vectorizer.fit_transform(text_data)
        self.case_ids = cases["id"].tolist()

        logger.info(f"TF-IDF search model trained on {len(cases)} cases")

    def search(self, query: str, n_results: int = 20) -> List[Tuple[int, float]]:
        """
        Search cases using TF-IDF similarity

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of (case_id, score) tuples
        """
        if not query.strip() or self.case_vectors is None:
            return []

        # Vectorize query
        query_vector = self.vectorizer.transform([query])

        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.case_vectors)[0]

        # Get top results
        case_scores = list(zip(self.case_ids, similarities))
        case_scores = [x for x in case_scores if x[1] > 0]  # Filter out zero scores
        case_scores.sort(key=lambda x: x[1], reverse=True)

        return case_scores[:n_results]
