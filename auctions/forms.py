from django import forms
from django.contrib.auth.models import User
from .models import AuctionItem, Bid, UserProfile

class AuctionForm(forms.ModelForm):
    class Meta:
        model = AuctionItem
        fields = ['title', 'description', 'image', 'category', 'starting_price', 'end_time']
        widgets = {
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'country']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
