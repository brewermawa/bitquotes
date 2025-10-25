from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

from .models import Profile


class ProfileInline(admin.TabularInline):
    model = Profile
    can_delete = False
    verbose_name = "Perfil"

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    @admin.display(description="Nombre")
    def name(self, obj):
        return obj.profile
    
    @admin.display(description="Correo electrónico")
    def e_mail(self, obj):
        return obj.email
    
    @admin.display(description="Teléfono")
    def phone(self, obj):
        return obj.profile.formatted_phone()
    
    @admin.display(description="Celular")
    def cel_phone(self, obj):
        return obj.profile.formatted_cel_phone()
    
    @admin.display(description="Rol")
    def role(self, obj):
        return obj.profile.get_role_display()
    
    @admin.display(description="Administrador sistema")
    def admin(self, obj):
        return obj.is_staff
    
    admin.boolean = True
    
    list_display = ["name", "e_mail", "phone", "cel_phone", "role", "admin"]

    inlines = [ProfileInline]
