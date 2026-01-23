from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.db.models import Q, Count, Max
from .models import AuctionItem, Bid, Category, Payment, UserProfile
from .forms import AuctionForm, BidForm, UserProfileForm, UserUpdateForm
from .emails import (
    send_welcome_email,
    send_new_bid_notification,
    send_outbid_notification,
    send_auction_won_notification
)
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


def index(request):
    auctions = AuctionItem.objects.filter(
        is_active=True,
        end_time__gt=timezone.now()
    ).select_related('category', 'seller').order_by('-created_at')

    # Search functionality
    query = request.GET.get('q', '')
    if query:
        auctions = auctions.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        auctions = auctions.filter(category__slug=category_slug)

    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        auctions = auctions.filter(current_price__gte=min_price)
    if max_price:
        auctions = auctions.filter(current_price__lte=max_price)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    if sort in ['current_price', '-current_price', 'end_time', '-end_time', '-created_at']:
        auctions = auctions.order_by(sort)

    categories = Category.objects.annotate(
        auction_count=Count('auctions', filter=Q(auctions__is_active=True, auctions__end_time__gt=timezone.now()))
    )

    return render(request, 'auctions/index.html', {
        'auctions': auctions,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    })


def auction_detail(request, pk):
    auction = get_object_or_404(
        AuctionItem.objects.select_related('seller', 'category'),
        pk=pk
    )
    bids = auction.bids.select_related('bidder').order_by('-created_at')
    highest_bid = bids.first()

    is_winner = False
    payment_done = False
    auction_ended = timezone.now() > auction.end_time

    if request.user.is_authenticated and highest_bid and highest_bid.bidder == request.user:
        if auction_ended:
            is_winner = True
            if Payment.objects.filter(auction=auction, status='paid').exists():
                payment_done = True

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        if auction_ended:
            messages.error(request, 'This auction has ended.')
            return redirect('auction_detail', pk=pk)

        if request.user == auction.seller:
            messages.error(request, 'You cannot bid on your own auction.')
            return redirect('auction_detail', pk=pk)

        form = BidForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > auction.current_price:
                # Get previous highest bidder before creating new bid
                previous_highest = highest_bid

                # Create new bid
                new_bid = Bid.objects.create(
                    auction=auction,
                    bidder=request.user,
                    amount=amount
                )
                auction.current_price = amount
                auction.save()

                # Send email notifications
                send_new_bid_notification(auction, new_bid)
                if previous_highest and previous_highest.bidder != request.user:
                    send_outbid_notification(auction, previous_highest.bidder, amount)

                messages.success(request, f'Your bid of {auction.currency} {amount} has been placed!')
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
        'payment_done': payment_done,
        'auction_ended': auction_ended,
    })


@login_required
def create_auction(request):
    if request.method == 'POST':
        form = AuctionForm(request.POST, request.FILES)
        if form.is_valid():
            auction = form.save(commit=False)
            auction.seller = request.user
            auction.current_price = auction.starting_price
            auction.save()
            messages.success(request, 'Your auction has been created!')
            return redirect('auction_detail', pk=auction.pk)
    else:
        form = AuctionForm()
    return render(request, 'auctions/create_auction.html', {'form': form})


@login_required
def edit_auction(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk, seller=request.user)

    # Can only edit if no bids yet
    if auction.bids.exists():
        messages.error(request, 'Cannot edit an auction that has bids.')
        return redirect('auction_detail', pk=pk)

    if request.method == 'POST':
        form = AuctionForm(request.POST, request.FILES, instance=auction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your auction has been updated!')
            return redirect('auction_detail', pk=pk)
    else:
        form = AuctionForm(instance=auction)

    return render(request, 'auctions/edit_auction.html', {'form': form, 'auction': auction})


@login_required
def delete_auction(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk, seller=request.user)

    # Can only delete if no bids yet
    if auction.bids.exists():
        messages.error(request, 'Cannot delete an auction that has bids.')
        return redirect('auction_detail', pk=pk)

    if request.method == 'POST':
        auction.delete()
        messages.success(request, 'Your auction has been deleted.')
        return redirect('dashboard')

    return render(request, 'auctions/delete_auction.html', {'auction': auction})


@login_required
def dashboard(request):
    user = request.user

    # My active auctions
    my_auctions = AuctionItem.objects.filter(seller=user).select_related('category').order_by('-created_at')
    active_auctions = my_auctions.filter(is_active=True, end_time__gt=timezone.now())
    ended_auctions = my_auctions.filter(Q(is_active=False) | Q(end_time__lte=timezone.now()))

    # My bids
    my_bids = Bid.objects.filter(bidder=user).select_related('auction').order_by('-created_at')

    # Auctions where I'm the highest bidder
    winning_bids = []
    for bid in my_bids:
        highest = bid.auction.bids.order_by('-amount').first()
        if highest and highest.bidder == user:
            winning_bids.append(bid.auction)
    winning_bids = list(set(winning_bids))  # Remove duplicates

    # Won auctions (ended and I'm highest bidder)
    won_auctions = [
        a for a in winning_bids
        if timezone.now() > a.end_time
    ]

    # Auctions I need to pay for
    pending_payments = [
        a for a in won_auctions
        if not Payment.objects.filter(auction=a, buyer=user, status='paid').exists()
    ]

    return render(request, 'auctions/dashboard.html', {
        'active_auctions': active_auctions,
        'ended_auctions': ended_auctions,
        'my_bids': my_bids[:10],  # Last 10 bids
        'winning_bids': [a for a in winning_bids if timezone.now() <= a.end_time],
        'won_auctions': won_auctions,
        'pending_payments': pending_payments,
    })


@login_required
def profile(request):
    user = request.user
    # Get or create profile
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=user_profile)

    # Stats
    total_auctions = AuctionItem.objects.filter(seller=user).count()
    total_bids = Bid.objects.filter(bidder=user).count()
    auctions_won = 0

    # Count won auctions
    user_bids = Bid.objects.filter(bidder=user).select_related('auction')
    for bid in user_bids:
        if bid.auction.end_time < timezone.now():
            highest = bid.auction.bids.order_by('-amount').first()
            if highest and highest.bidder == user:
                auctions_won += 1

    return render(request, 'auctions/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'total_auctions': total_auctions,
        'total_bids': total_bids,
        'auctions_won': auctions_won,
    })


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            # Send welcome email
            if user.email:
                send_welcome_email(user)
            login(request, user)
            messages.success(request, 'Welcome to SmallAuctions!')
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
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'auctions/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')


def category_list(request):
    categories = Category.objects.annotate(
        auction_count=Count('auctions', filter=Q(auctions__is_active=True, auctions__end_time__gt=timezone.now()))
    ).order_by('name')
    return render(request, 'auctions/category_list.html', {'categories': categories})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    auctions = AuctionItem.objects.filter(
        category=category,
        is_active=True,
        end_time__gt=timezone.now()
    ).select_related('seller').order_by('-created_at')

    return render(request, 'auctions/category_detail.html', {
        'category': category,
        'auctions': auctions,
    })


@login_required
def create_checkout_session(request, pk):
    auction = get_object_or_404(AuctionItem, pk=pk)

    # Verify winner
    highest_bid = auction.bids.order_by('-amount').first()
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
