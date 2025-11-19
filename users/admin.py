from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomUser
from .models import Profile


class ProfileInline(admin.TabularInline):
    model = Profile
    verbose_name = "Perfil"
    verbose_name_plural = "Perfiles"
    can_delete = False


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    @admin.display(description="Nombre")
    def name(self, obj):
        return obj.get_full_name() or obj.username
    
    @admin.display(description="Correo electrónico")
    def e_mail(self, obj):
        return obj.email
    
    @admin.display(description="Teléfono")
    def phone(self, obj):
        if hasattr(obj, "profile") and obj.profile.phone:
            return obj.profile.formatted_phone()
        
        return "-"
    
    @admin.display(description="Celular")
    def cel_phone(self, obj):
        if hasattr(obj, "profile") and obj.profile.cel_phone:
            return obj.profile.formatted_cel_phone()
        
        return "-"
    
    @admin.display(description="Rol")
    def role(self, obj):
        if hasattr(obj, "profile") and obj.profile.role:
            return obj.profile.get_role_display()
        
        return "-"
    
    @admin.display(description="Administrador sistema", boolean=True)
    def admin(self, obj):
        return obj.is_staff
    
    list_display = ["name", "e_mail", "phone", "cel_phone", "role", "admin"]
    search_fields = ["username", "email", "first_name", "last_name", "profile__phone", "profile__cel_phone"]
    list_filter = ["profile__role", "is_staff", "is_active", "is_superuser"]
    ordering = ["first_name", "last_name"]
    inlines = [ProfileInline]
