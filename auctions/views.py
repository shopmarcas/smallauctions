from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from .models import AuctionItem, Bid, Category, Payment
from .forms import AuctionForm, BidForm
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    auctions = AuctionItem.objects.filter(is_active=True, end_time__gt=timezone.now()).order_by('-created_at')
    return render(request, 'auctions/index.html', {'auctions': auctions})

def auction_detail(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk)
    bids = auction.bids.order_by('-created_at')
    highest_bid = bids.first()
    
    is_winner = False
    payment_done = False
    
    if request.user.is_authenticated and highest_bid and highest_bid.bidder == request.user:
        if timezone.now() > auction.end_time:
            is_winner = True
            if Payment.objects.filter(auction=auction, status='paid').exists():
                payment_done = True
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        form = BidForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > auction.current_price:
                Bid.objects.create(auction=auction, bidder=request.user, amount=amount)
                auction.current_price = amount
                auction.save()
                return redirect('auction_detail', pk=pk)
            else:
                form.add_error('amount', 'Bid must be higher than current price')
    else:
        form = BidForm()

    return render(request, 'auctions/auction_detail.html', {
        'auction': auction,
        'bids': bids,
        'form': form,
        'is_winner': is_winner,
        'payment_done': payment_done
    })

@login_required
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user
            auction.current_price = auction.starting_price
            auction.save()
            return redirect('auction_detail', pk=auction.pk)
    else:
        form = AuctionForm()
    return render(request, 'auctions/create_auction.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'auctions/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'auctions/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def create_checkout_session(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk)
    
    # Verify winner
    highest_bid = auction.bids.order_by('-created_at').first()
    if not highest_bid or highest_bid.bidder != request.user or timezone.now() <= auction.end_time:
        return redirect('auction_detail', pk=pk)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': auction.currency.lower(),
                'product_data': {
                    'name': auction.title,
                },
                'unit_amount': int(auction.current_price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('payment_success', args=[pk])) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('auction_detail', args=[pk])),
    )
    
    return redirect(session.url, code=303)

@login_required
def payment_success(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk)
    session_id = request.GET.get('session_id')
    
    if session_id:
        # In a real app, verify session with Stripe
        Payment.objects.create(
            auction=auction,
            buyer=request.user,
            stripe_payment_id=session_id,
            amount=auction.current_price,
            currency=auction.currency,
            status='paid'
        )
        auction.is_active = False
        auction.save()
        
    return render(request, 'auctions/payment_success.html', {'auction': auction})
