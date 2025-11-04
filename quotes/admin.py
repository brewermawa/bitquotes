from django.contrib import admin


from .models import Quote, QuoteLine, QuoteComment

class QuoteLineInline(admin.StackedInline):
    model = QuoteLine
    extra = 0
    readonly_fields = ["description", "unit_price", "section"]

class QuoteCommentInLine(admin.TabularInline):
    model = QuoteComment
    readonly_fields = ["user", "comment"]
    extra = 0
    can_delete = False

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["quote_id", "customer", "contact", "user", "status", "total"]
    list_filter = ["customer", "user", "status", "is_active"]
    date_hierarchy = "created"
    inlines = [QuoteLineInline, QuoteCommentInLine]
    fieldsets = (
        (None, {
            "fields": (
                "quote_id", "user", "status", "payment_terms", "valid_until",
                "is_active"
            )
        }),
        ('Información cliente', {
            "fields": ("customer", "contact")
        }),
        ('Totales', {
            "fields": ("sub_total", "discount_total", "tax", "total")
        }),
        ('Fecha y usuario de creación', {
            'classes': ('collapse',),
            "fields": ("created", "updated", "created_by", "updated_by")
        }),
    )

    readonly_fields = [
        "quote_id", "valid_until", "sub_total", "discount_total", "tax",
        "total", "created", "updated", "created_by", "updated_by"
    ]


