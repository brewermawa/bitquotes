from django.contrib import admin

from .models import Customer, Contact

class ContactInline(admin.StackedInline):
    model = Contact
    verbose_name = "Contacto"
    verbose_name_plural = "Contactos"
    exclude = ["created_by", "updated_by"]
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    @admin.display(description="Nombre")
    def name(self, obj):
        return obj.name
    
    @admin.display(description="RFC", ordering="rfc")
    def formatted_rfc(self, obj):
        return obj.formatted_rfc()
    
    list_display = ["name", "formatted_rfc", "assigned_to"]
    list_editable = ["assigned_to"]
    list_filter = [("assigned_to", admin.RelatedOnlyFieldListFilter)]
    search_fields = ["name", "rfc"]
    search_help_text = "Búsqueda por nombre de cliente o RFC"
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created", "updated", "created_by", "updated_by"]
    empty_value_display = "-"
    list_select_related = ("assigned_to",)
    list_per_page = 50
    inlines = [ContactInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.updated_by = request.user

        return super().save_model(request, obj, form, change)