from django.contrib import admin
from .models import UserProfile, Category, AuctionItem, Bid, Payment

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(AuctionItem)
admin.site.register(Bid)
admin.site.register(Payment)
