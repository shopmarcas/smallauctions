from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_welcome_email(user):
    """Send welcome email after user registration."""
    subject = 'Welcome to SmallAuctions!'
    message = f"""
Hi {user.username},

Welcome to SmallAuctions! We're excited to have you join our community.

With SmallAuctions, you can:
- Browse and bid on auctions with 0% fees
- Create your own auctions to sell items
- Track your bids and auctions in your dashboard

Get started by browsing our active auctions or creating your first listing.

Happy bidding!
The SmallAuctions Team
"""
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )


def send_new_bid_notification(auction, bid):
    """Notify seller when a new bid is placed on their auction."""
    subject = f'New bid on your auction: {auction.title}'
    message = f"""
Hi {auction.seller.username},

Great news! Someone placed a new bid on your auction.

Auction: {auction.title}
New Bid Amount: {auction.currency} {bid.amount}
Bidder: {bid.bidder.username}

Your auction ends on {auction.end_time.strftime('%B %d, %Y at %H:%M UTC')}.

View your auction to see all the activity.

Best,
The SmallAuctions Team
"""
    if auction.seller.email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [auction.seller.email],
            fail_silently=True,
        )


def send_outbid_notification(auction, previous_bidder, new_amount):
    """Notify previous highest bidder that they've been outbid."""
    subject = f'You\'ve been outbid on: {auction.title}'
    message = f"""
Hi {previous_bidder.username},

Someone has placed a higher bid on the auction you were winning.

Auction: {auction.title}
New Highest Bid: {auction.currency} {new_amount}

Don't miss out! Place a new bid to get back in the lead.

The auction ends on {auction.end_time.strftime('%B %d, %Y at %H:%M UTC')}.

Best,
The SmallAuctions Team
"""
    if previous_bidder.email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [previous_bidder.email],
            fail_silently=True,
        )


def send_auction_won_notification(auction, winner):
    """Notify the winner when an auction ends."""
    subject = f'Congratulations! You won the auction: {auction.title}'
    message = f"""
Hi {winner.username},

Congratulations! You've won the auction for "{auction.title}"!

Winning Bid: {auction.currency} {auction.current_price}

Please complete your payment to finalize the purchase.

Best,
The SmallAuctions Team
"""
    if winner.email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [winner.email],
            fail_silently=True,
        )


def send_auction_ended_seller_notification(auction, winner=None):
    """Notify seller when their auction ends."""
    if winner:
        subject = f'Your auction has ended: {auction.title}'
        message = f"""
Hi {auction.seller.username},

Your auction for "{auction.title}" has ended!

Final Price: {auction.currency} {auction.current_price}
Winner: {winner.username}

The buyer has been notified to complete their payment.

Best,
The SmallAuctions Team
"""
    else:
        subject = f'Your auction has ended without bids: {auction.title}'
        message = f"""
Hi {auction.seller.username},

Your auction for "{auction.title}" has ended without any bids.

Consider relisting the item with a lower starting price or better description.

Best,
The SmallAuctions Team
"""
    if auction.seller.email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [auction.seller.email],
            fail_silently=True,
        )
