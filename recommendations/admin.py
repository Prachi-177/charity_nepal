from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display

from charity_backend.admin import admin_site
from .models import (
    AlgorithmPerformance,
    CaseFeatures, 
    RecommendationFeedback, 
    RecommendationHistory, 
    RecommendationModel,
    SearchQuery,
    UserProfile,
    UserRecommendation
)


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """Admin configuration for UserProfile model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = ("user_info", "demographics", "interests_display", "donation_behavior", "created_at")
    list_filter = (
        "age_range",
        "income_range",
        ("created_at", admin.DateFieldListFilter)
    )
    search_fields = ("user__email", "user__first_name", "user__last_name", "interests")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {
            "fields": ("user",),
            "classes": ("tab",)
        }),
        ("Demographics", {
            "fields": ("age_range", "income_range", "location_preference"),
            "classes": ("tab",)
        }),
        ("Preferences", {
            "fields": ("interests", "preferred_categories", "preferred_donation_amount", "donation_frequency"),
            "classes": ("tab",)
        }),
        ("Behavior", {
            "fields": ("total_donated", "total_donations", "avg_donation_amount", "last_donation_date"),
            "classes": ("tab",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("tab",)
        }),
    )

    @display(description="User", ordering="user__first_name")
    def user_info(self, obj):
        """Display user information"""
        name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return format_html(
            '<div class="flex items-center space-x-3">'
            '<div class="w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-semibold">'
            '{}'
            '</div>'
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-sm text-gray-500">{}</span>'
            '</div>'
            '</div>',
            name[0].upper(),
            name,
            obj.user.email
        )

    @display(description="Demographics")
    def demographics(self, obj):
        """Display demographic information"""
        parts = []
        if obj.age_range:
            parts.append(obj.age_range)
        if obj.income_range:
            parts.append(obj.get_income_range_display())
        if obj.location_preference:
            parts.append(obj.location_preference)
            
        return format_html(
            '<div class="flex flex-col text-sm">'
            '{}'
            '</div>',
            '<br>'.join(parts) if parts else 'Not specified'
        )

    @display(description="Interests")
    def interests_display(self, obj):
        """Display interests"""
        if obj.interests:
            interests = obj.interests.split(',')[:3]  # Show first 3 interests
            return format_html(
                '<div class="flex flex-wrap gap-1">'
                '{}'
                '</div>',
                ''.join([f'<span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">{interest.strip()}</span>' 
                        for interest in interests])
            )
        return "Not specified"

    @display(description="Donation Pattern")
    def donation_behavior(self, obj):
        """Display donation behavior"""
        return format_html(
            '<div class="flex flex-col text-sm">'
            '<span class="font-semibold">NPR {:,.0f}</span>'
            '<span class="text-gray-500">{} donations</span>'
            '<span class="text-xs text-gray-400">Avg: NPR {:,.0f}</span>'
            '</div>',
            obj.total_donated or 0,
            obj.total_donations or 0,
            obj.avg_donation_amount or 0
        )


@admin.register(RecommendationHistory)
class RecommendationHistoryAdmin(ModelAdmin):
    """Admin configuration for RecommendationHistory model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = ("user_info", "recommended_cases_count", "algorithm_used", "created_at")
    list_filter = (
        "algorithm_used",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("user__email", "user__first_name", "user__last_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @display(description="User", ordering="user__first_name")
    def user_info(self, obj):
        """Display user information"""
        name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<div class="w-6 h-6 bg-purple-100 text-purple-800 rounded-full flex items-center justify-center text-xs font-semibold">'
            '{}'
            '</div>'
            '<span class="font-medium">{}</span>'
            '</div>',
            name[0].upper(),
            name
        )

    @display(description="Cases Recommended")
    def recommended_cases_count(self, obj):
        """Display number of recommended cases"""
        import json
        try:
            recommended_cases = json.loads(obj.recommended_cases) if obj.recommended_cases else []
            count = len(recommended_cases)
            return format_html(
                '<span class="inline-flex items-center px-2 py-1 rounded-full text-sm bg-blue-100 text-blue-700">'
                '{} cases'
                '</span>',
                count
            )
        except:
            return "0 cases"


@admin.register(RecommendationModel)
class RecommendationModelAdmin(ModelAdmin):
    """Admin configuration for RecommendationModel model"""

    # Unfold specific settings
    compressed_fields = True
    warn_unsaved_form = True

    list_display = ("name_badge", "model_type", "version_info", "performance", "status_badge", "training_date")
    list_filter = ("model_type", "is_active", "training_date")
    search_fields = ("name", "model_type", "version")
    ordering = ("-training_date",)
    readonly_fields = ("training_date", "last_used")

    @display(description="Model", ordering="name")
    def name_badge(self, obj):
        """Display model name with icon"""
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<span class="text-lg">🤖</span>'
            '<span class="font-semibold">{}</span>'
            '</div>',
            obj.name
        )

    @display(description="Version & Algorithm")
    def version_info(self, obj):
        """Display version and algorithm information"""
        return format_html(
            '<div class="flex flex-col text-sm">'
            '<span class="font-medium">v{}</span>'
            '<span class="text-gray-500">{}</span>'
            '</div>',
            obj.version,
            obj.model_type
        )

    @display(description="Performance")
    def performance(self, obj):
        """Display performance metrics"""
        accuracy = obj.accuracy or 0
        color = "text-green-600" if accuracy > 0.8 else "text-yellow-600" if accuracy > 0.6 else "text-red-600"
        
        return format_html(
            '<div class="flex flex-col text-sm">'
            '<span class="font-semibold {}">Accuracy: {:.2%}</span>'
            '</div>',
            color,
            accuracy
        )

    @display(description="Status", boolean=True, ordering="is_active")
    def status_badge(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">'
                '✅ Active'
                '</span>'
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">'
            '⏸️ Inactive'
            '</span>'
        )


@admin.register(CaseFeatures)
class CaseFeaturesAdmin(ModelAdmin):
    """Admin configuration for CaseFeatures model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = ("case_link", "category_badge", "urgency_score", "popularity_score", "last_updated")
    list_filter = (
        "case__category",
        "case__urgency_flag",
        ("last_updated", admin.DateFieldListFilter),
    )
    search_fields = ("case__title", "case__beneficiary_name")
    ordering = ("-last_updated",)
    readonly_fields = ("last_updated",)

    @display(description="Case", ordering="case__title")
    def case_link(self, obj):
        """Display case title as link"""
        return format_html(
            '<a href="/admin/cases/charitycase/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">{}</a>',
            obj.case.id,
            obj.case.title[:50] + "..." if len(obj.case.title) > 50 else obj.case.title
        )

    @display(description="Category", ordering="case__category")
    def category_badge(self, obj):
        """Display case category"""
        category_colors = {
            'cancer': 'bg-red-100 text-red-800',
            'accident': 'bg-orange-100 text-orange-800',
            'education': 'bg-blue-100 text-blue-800',
            'medical': 'bg-green-100 text-green-800',
            'disaster': 'bg-purple-100 text-purple-800',
            'other': 'bg-gray-100 text-gray-800',
        }
        
        color = category_colors.get(obj.case.category, 'bg-gray-100 text-gray-800')
        
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '{}'
            '</span>',
            color,
            obj.case.get_category_display()
        )

    @display(description="Urgency Score")
    def urgency_score(self, obj):
        """Display urgency score"""
        score = obj.urgency_score or 0
        color = "text-red-600" if score > 0.8 else "text-yellow-600" if score > 0.5 else "text-green-600"
        
        return format_html(
            '<span class="font-semibold {}">{:.2f}</span>',
            color,
            score
        )

    @display(description="Popularity Score")
    def popularity_score(self, obj):
        """Display popularity score"""
        score = obj.view_count / 100.0  # Simple popularity calculation
        return format_html(
            '<span class="font-semibold text-blue-600">{:.2f}</span>',
            score
        )


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(ModelAdmin):
    """Admin configuration for RecommendationFeedback model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = ("user_info", "case_link", "feedback_badge", "created_at")
    list_filter = (
        "feedback_type",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("user__email", "case__title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @display(description="User", ordering="user__first_name")
    def user_info(self, obj):
        """Display user information"""
        name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<div class="w-6 h-6 bg-green-100 text-green-800 rounded-full flex items-center justify-center text-xs font-semibold">'
            '{}'
            '</div>'
            '<span class="font-medium">{}</span>'
            '</div>',
            name[0].upper(),
            name
        )

    @display(description="Case", ordering="case__title")
    def case_link(self, obj):
        """Display case title as link"""
        return format_html(
            '<a href="/admin/cases/charitycase/{}/change/" class="text-blue-600 hover:text-blue-800 font-medium">{}</a>',
            obj.case.id,
            obj.case.title[:40] + "..." if len(obj.case.title) > 40 else obj.case.title
        )

    @display(description="Feedback", ordering="feedback_type")
    def feedback_badge(self, obj):
        """Display feedback type"""
        feedback_config = {
            'like': {'color': 'bg-green-100 text-green-800', 'icon': '👍'},
            'dislike': {'color': 'bg-red-100 text-red-800', 'icon': '👎'},
            'not_interested': {'color': 'bg-yellow-100 text-yellow-800', 'icon': '�'},
            'irrelevant': {'color': 'bg-gray-100 text-gray-800', 'icon': '❌'},
        }
        
        config = feedback_config.get(obj.feedback_type, feedback_config['like'])
        
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">'
            '<span class="mr-1">{}</span>{}'
            '</span>',
            config['color'],
            config['icon'],
            obj.get_feedback_type_display()
        )


@admin.register(SearchQuery)
class SearchQueryAdmin(ModelAdmin):
    """Admin configuration for SearchQuery model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = ("search_info", "user_info", "results_count", "created_at")
    list_filter = (
        ("created_at", admin.DateFieldListFilter),
        ("user", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("query", "user__email", "category_filter")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @display(description="Search Query", ordering="query")
    def search_info(self, obj):
        """Display search query information"""
        query = obj.query[:50] + "..." if len(obj.query) > 50 else obj.query
        return format_html(
            '<div class="flex items-center space-x-2">'
            '<span class="text-lg">🔍</span>'
            '<div class="flex flex-col">'
            '<span class="font-medium">{}</span>'
            '<span class="text-xs text-gray-500">Session: {}</span>'
            '</div>'
            '</div>',
            query,
            "Anonymous" if not obj.user else "User session"
        )

    @display(description="User", ordering="user__first_name")
    def user_info(self, obj):
        """Display user information"""
        if obj.user:
            name = f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
            return format_html(
                '<div class="flex items-center space-x-2">'
                '<div class="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-semibold">'
                '{}'
                '</div>'
                '<span class="font-medium">{}</span>'
                '</div>',
                name[0].upper(),
                name
            )
        return format_html(
            '<span class="text-gray-500 italic">Anonymous User</span>'
        )

    @display(description="Results")
    def results_count(self, obj):
        """Display results count"""
        count = obj.results_count or 0
        color = "text-green-600" if count > 0 else "text-red-600"
        
        return format_html(
            '<span class="font-semibold {}">{} results</span>',
            color,
            count
        )


@admin.register(UserRecommendation)
class UserRecommendationAdmin(ModelAdmin):
    """Admin configuration for UserRecommendation model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "user_info",
        "case_info", 
        "algorithm_badge",
        "confidence_display",
        "interaction_status",
        "created_at"
    )
    list_filter = (
        "algorithm_used",
        "is_viewed",
        "is_clicked", 
        "is_donated",
        ("created_at", admin.DateFieldListFilter)
    )
    search_fields = (
        "user__email",
        "user__first_name", 
        "user__last_name",
        "recommended_case__title"
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "viewed_at",
        "clicked_at", 
        "donated_at"
    )

    fieldsets = (
        ("Recommendation Info", {
            "fields": ("user", "recommended_case", "algorithm_used", "confidence_score"),
            "classes": ("tab",)
        }),
        ("Interactions", {
            "fields": ("is_viewed", "viewed_at", "is_clicked", "clicked_at", "is_donated", "donated_at"),
            "classes": ("tab",)
        }),
        ("Context", {
            "fields": ("recommendation_context",),
            "classes": ("tab",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("tab",)
        })
    )

    @display(description="User")
    def user_info(self, obj):
        """Display user information"""
        user = obj.user
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-semibold">{} {}</span>'
            '<span class="text-xs text-gray-500">{}</span>'
            '</div>',
            user.first_name,
            user.last_name,
            user.email
        )

    @display(description="Case")
    def case_info(self, obj):
        """Display case information"""
        case = obj.recommended_case
        return format_html(
            '<div class="flex flex-col">'
            '<span class="font-semibold">{}</span>'
            '<span class="text-xs text-gray-500">NPR {:,.0f}</span>'
            '</div>',
            case.title[:50] + ("..." if len(case.title) > 50 else ""),
            case.target_amount
        )

    @display(description="Algorithm") 
    def algorithm_badge(self, obj):
        """Display algorithm with colored badge"""
        algorithm_colors = {
            'content_based': 'bg-blue-100 text-blue-800',
            'collaborative': 'bg-green-100 text-green-800',
            'hybrid': 'bg-purple-100 text-purple-800',
            'category_based': 'bg-yellow-100 text-yellow-800',
            'popularity': 'bg-red-100 text-red-800'
        }
        
        color_class = algorithm_colors.get(obj.algorithm_used, 'bg-gray-100 text-gray-800')
        
        return format_html(
            '<span class="px-2 py-1 rounded text-xs font-medium {}">{}</span>',
            color_class,
            obj.get_algorithm_used_display()
        )

    @display(description="Confidence", ordering="confidence_score")
    def confidence_display(self, obj):
        """Display confidence score with progress indicator"""
        score = obj.confidence_score * 100
        color = "text-green-600" if score >= 80 else "text-yellow-600" if score >= 60 else "text-red-600"
        
        return format_html(
            '<div class="flex items-center">'
            '<div class="w-12 bg-gray-200 rounded-full h-2 mr-2">'
            '<div class="bg-current h-2 rounded-full {}" style="width: {:.0f}%"></div>'
            '</div>'
            '<span class="text-xs {}">{:.0f}%</span>'
            '</div>',
            color,
            score,
            color,
            score
        )

    @display(description="Status")
    def interaction_status(self, obj):
        """Display interaction status with badges"""
        statuses = []
        
        if obj.is_donated:
            statuses.append('<span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">Donated</span>')
        elif obj.is_clicked:
            statuses.append('<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Clicked</span>')
        elif obj.is_viewed:
            statuses.append('<span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">Viewed</span>')
        else:
            statuses.append('<span class="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">No Interaction</span>')
            
        return format_html('<div class="flex flex-wrap gap-1">{}</div>', ' '.join(statuses))


@admin.register(AlgorithmPerformance)
class AlgorithmPerformanceAdmin(ModelAdmin):
    """Admin configuration for AlgorithmPerformance model"""

    # Unfold specific settings
    compressed_fields = True
    list_select_related = True
    warn_unsaved_form = True

    list_display = (
        "algorithm_name",
        "date",
        "performance_metrics",
        "ctr_display",
        "conversion_display"
    )
    list_filter = (
        "algorithm_name",
        ("date", admin.DateFieldListFilter)
    )
    search_fields = ("algorithm_name",)
    ordering = ("-date", "algorithm_name")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Algorithm Info", {
            "fields": ("algorithm_name", "date"),
            "classes": ("tab",)
        }),
        ("Performance Metrics", {
            "fields": (
                "total_recommendations",
                "clicked_recommendations", 
                "donated_recommendations",
                "click_through_rate",
                "conversion_rate",
                "avg_confidence_score"
            ),
            "classes": ("tab",)
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("tab",)
        })
    )

    @display(description="Metrics")
    def performance_metrics(self, obj):
        """Display performance metrics summary"""
        return format_html(
            '<div class="flex flex-col text-xs">'
            '<span>📊 {} total</span>'
            '<span>👆 {} clicks</span>'
            '<span>💰 {} donations</span>'
            '</div>',
            obj.total_recommendations,
            obj.clicked_recommendations,
            obj.donated_recommendations
        )

    @display(description="CTR", ordering="click_through_rate")
    def ctr_display(self, obj):
        """Display click-through rate with color coding"""
        ctr = obj.click_through_rate
        color = "text-green-600" if ctr >= 5 else "text-yellow-600" if ctr >= 2 else "text-red-600"
        
        return format_html(
            '<span class="font-semibold {}">{:.2f}%</span>',
            color,
            ctr
        )

    @display(description="Conversion", ordering="conversion_rate")
    def conversion_display(self, obj):
        """Display conversion rate with color coding"""
        conversion = obj.conversion_rate
        color = "text-green-600" if conversion >= 10 else "text-yellow-600" if conversion >= 5 else "text-red-600"
        
        return format_html(
            '<span class="font-semibold {}">{:.2f}%</span>',
            color,
            conversion
        )
