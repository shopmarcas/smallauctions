from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile, Category, AuctionItem, Bid, Payment


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'country', 'created_at')
    list_filter = ('country', 'created_at')
    search_fields = ('user__username', 'user__email', 'display_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'auction_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def auction_count(self, obj):
        return obj.auctions.filter(is_active=True, end_time__gt=timezone.now()).count()
    auction_count.short_description = 'Active Auctions'


@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'current_price', 'bid_count', 'status_badge', 'end_time')
    list_filter = ('is_active', 'category', 'created_at', 'end_time')
    search_fields = ('title', 'description', 'seller__username')
    readonly_fields = ('current_price', 'created_at', 'updated_at', 'image_preview')
    raw_id_fields = ('seller',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'image', 'image_preview', 'category')
        }),
        ('Pricing', {
            'fields': ('starting_price', 'current_price', 'currency')
        }),
        ('Seller & Timing', {
            'fields': ('seller', 'start_time', 'end_time', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def bid_count(self, obj):
        return obj.bids.count()
    bid_count.short_description = 'Bids'

    def status_badge(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        elif now > obj.end_time:
            return format_html('<span style="color: red;">Ended</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')
    status_badge.short_description = 'Status'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount', 'created_at', 'is_winning')
    list_filter = ('created_at', 'auction__category')
    search_fields = ('auction__title', 'bidder__username')
    raw_id_fields = ('auction', 'bidder')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def is_winning(self, obj):
        highest_bid = obj.auction.bids.order_by('-amount').first()
        if highest_bid and highest_bid.id == obj.id:
            return format_html('<span style="color: green;">Yes</span>')
        return format_html('<span style="color: gray;">No</span>')
    is_winning.short_description = 'Winning Bid'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('auction', 'buyer', 'amount', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('auction__title', 'buyer__username', 'stripe_payment_id')
    raw_id_fields = ('auction', 'buyer')
    readonly_fields = ('stripe_payment_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Status'


# Customize admin site headers
admin.site.site_header = 'SmallAuctions Admin'
admin.site.site_title = 'SmallAuctions'
admin.site.index_title = 'Admin Dashboard'
