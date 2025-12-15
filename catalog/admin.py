from django.contrib import admin

from .models import Category, Product, RelatedProduct, ProductDocument


class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    verbose_name = "Producto relacionado"
    fk_name = "product"
    autocomplete_fields = ["related_product"]
    extra = 0
    exclude = ["created", "updated", "created_by", "updated_by"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "related_product":
            obj_id = request.resolver_match.kwargs.get("object_id")

            if obj_id:
                kwargs["queryset"] = Product.objects.exclude(pk=obj_id)
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    verbose_name = "Documento de producto"
    extra = 0
    exclude = ["created", "updated", "created_by", "updated_by"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    list_editable = ["is_active"]
    readonly_fields = ["created_by", "updated_by"]
    list_filter = ["is_active"]
    search_fields = ["name"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.updated_by = request.user

        return super().save_model(request, obj, form, change)
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "category", "price", "price_editable", "product_type", "is_active"]
    list_display_links = ["sku", "name"]
    list_filter  =["category", "product_type"]
    list_editable = ["price", "price_editable", "is_active"]
    search_fields = ["sku", "name"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_by", "updated_by"]
    inlines = [RelatedProductInline, ProductDocumentInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user

        obj.updated_by = request.user

        return super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if hasattr(instance, "created_by") and instance.pk is None:
                instance.created_by = request.user

            if hasattr(instance, "updated_by"):
                instance.updated_by = request.user

            instance.save()
        formset.save_m2m()
        
