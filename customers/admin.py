from django.contrib import admin

from .models import Customer, Contact

class ContactInline(admin.StackedInline):
    model = Contact
    verbose_name = "Contacto"
    exclude = ["created_by", "updated_by"]
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    @admin.display(description="Nombre")
    def name(self, obj):
        return obj.name
    
    @admin.display(description="RFC")
    def formatted_rfc(self, obj):
        return obj.formatted_rfc()
    
    list_display = ["name", "formatted_rfc", "assigned_to"]
    list_editable = ["assigned_to"]
    list_filter = ["assigned_to"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created", "updated", "created_by", "updated_by"]
    empty_value_display = "-"
    inlines = [ContactInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.updated_by = request.user

        return super().save_model(request, obj, form, change)