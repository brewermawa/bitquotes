from django.contrib import admin


from .models import Quote, QuoteLine, QuoteComment

class QuoteLineInline(admin.StackedInline):
    model = QuoteLine
    extra = 0
    #fields = ["product", "description", "quantity", "unit_price"]
    readonly_fields = ["product", "description", "quantity", "unit_price", "section", "discount", "delivery_time"]
    can_delete = False
    show_change_link = False

    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False


class QuoteCommentInline(admin.TabularInline):
    model = QuoteComment
    readonly_fields = ["user", "created"]
    extra = 0
    can_delete = False
    show_change_link = False
    
    #def has_add_permission(self, request, obj=None): return False
    #def has_change_permission(self, request, obj=None): return False

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            instance.user = request.user

            instance.save()


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["quote_id", "customer", "contact", "user", "status", "created"]
    list_display_links = ["quote_id"]
    search_fields = ["quote_id", "customer__name", "contact__first_name", "contact__last_name", "user__first_name", "user__last_name"]
    list_filter = ["customer", "user", "status", "is_active"]
    list_select_related = ["customer", "contact", "user"]
    date_hierarchy = "created"
    ordering = ["-created"]
    empty_value_display = "-"
    readonly_fields = [
        "quote_id", "user", "status", "payment_terms", "valid_until", "is_active", "customer", "contact",
        "approved_by", "approved_at", "sent_by", "sent_at",
        "won_by", "won_at", "lost_by", "lost_at", "lost_reason", "created", "updated", "created_by",
        "updated_by",
    ]
    
    fieldsets = (
        (None, {
            "fields": (
                "quote_id", "user", "status", "payment_terms", "valid_until", "is_active"
            )
        }),
        ('Información cliente', {"fields": ("customer", "contact")}),
        #('Totales', {"fields": ("sub_total", "discount_total", "tax", "total")}),
        ("Workflow", {
            "classes": ("collapse",),
            "fields": ("approved_by", "approved_at", "sent_by", "sent_at", "won_by", "won_at", "lost_by", "lost_at", "lost_reason"),
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created", "updated", "created_by", "updated_by"),
        }),
    )

    inlines = [QuoteLineInline, QuoteCommentInline]

    #def has_add_permission(self, request): return False
    #def has_change_permission(self, request, obj=None): return False
    #def has_delete_permission(self, request, obj=None): return False

    


