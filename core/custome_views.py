from django.contrib import admin

class ReadOnlyModelAdmin(admin.ModelAdmin):
    """Mixin for admins that should only allow viewing. not editing."""

    def get_readonly_fields(self, request, obj = ...):
        return [field.name for field in self.model._meta.fields]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = ...):
        opts= self.model._meta
        if f"/admin/{opts.app_label}/{opts.model_name}/" in request.path:
            return False
        return True
    
    def get_actions(self, request):
        action = super().get_actions(request)
        action.pop('delete_selected', None)
        return action

