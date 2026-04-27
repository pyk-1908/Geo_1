from django.contrib import admin
from siapp.models import (Customer, User, CustomerPeriod, Buyer, Country, ItemsToCustomerPeriods, Year, GeoCoordinates, ProductGroup, ProductCluster, Region, Industry)


# Customer has ManyToMany relationship with Supplier, so we create an inline for Supplier

class GroupsInline(admin.StackedInline):
    model = User.groups.through
    extra = 1

# Customizes admin forms and list displays for Customer, User and CustomerPeriod models

class UserAdmin(admin.ModelAdmin):
    fields = ["username", "first_name", "last_name", "email", "customer", "allowed_product_clusters"]
    list_display = ["username", "first_name", "last_name", "email", "customer"]
    filter_horizontal = ["allowed_product_clusters"]
    inlines = [GroupsInline]

class CustomerPeriodAdmin(admin.ModelAdmin):
    fields = ["name", "begin", "end", "customer"]
    list_display = fields


# For the following models, create list displays that include all fields (except "id")
class CountryAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in Country._meta.fields if field.name != "id"]

class RegionAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in Region._meta.fields if field.name != "id"]

class BuyerAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in Buyer._meta.fields if field.name != "id"]

class ProductGroupAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in ProductGroup._meta.fields if field.name != "id"]

class industryAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in Industry._meta.fields if field.name != "id"]

class ItemsToCustomerPeriodsAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in ItemsToCustomerPeriods._meta.fields if field.name != "id"]

class YearAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in Year._meta.fields if field.name != "id"]

class GeoCoordinatesAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [field.name for field in GeoCoordinates._meta.fields if field.name != "id"]

# Registers models with the Django admin
admin.site.register(Year, YearAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(CustomerPeriod, CustomerPeriodAdmin)
admin.site.register(Buyer, BuyerAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)
admin.site.register(Industry, industryAdmin)
admin.site.register(ProductCluster)  # Simple registration due to having only one field.
admin.site.register(ItemsToCustomerPeriods, ItemsToCustomerPeriodsAdmin)
admin.site.register(GeoCoordinates, GeoCoordinatesAdmin)

