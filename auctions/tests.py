from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import UserProfile, Category, AuctionItem, Bid, Payment


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name='Test User',
            country='US'
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.display_name, 'Test User')
        self.assertEqual(self.profile.country, 'US')

    def test_profile_str(self):
        self.assertEqual(str(self.profile), 'Test User')

    def test_profile_str_without_display_name(self):
        self.profile.display_name = ''
        self.profile.save()
        self.assertEqual(str(self.profile), 'testuser')


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Electronics')
        self.assertEqual(self.category.slug, 'electronics')

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Electronics')


class AuctionItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.auction = AuctionItem.objects.create(
            title='Test Auction',
            description='A test auction item',
            seller=self.user,
            category=self.category,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )

    def test_auction_creation(self):
        self.assertEqual(self.auction.title, 'Test Auction')
        self.assertEqual(self.auction.seller, self.user)
        self.assertEqual(self.auction.starting_price, Decimal('100.00'))
        self.assertTrue(self.auction.is_active)

    def test_auction_str(self):
        self.assertEqual(str(self.auction), 'Test Auction')

    def test_auction_current_price_set_on_create(self):
        self.assertEqual(self.auction.current_price, self.auction.starting_price)


class BidModelTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.bidder = User.objects.create_user(
            username='bidder',
            password='testpass123'
        )
        self.auction = AuctionItem.objects.create(
            title='Test Auction',
            description='A test auction item',
            seller=self.seller,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )
        self.bid = Bid.objects.create(
            auction=self.auction,
            bidder=self.bidder,
            amount=Decimal('150.00')
        )

    def test_bid_creation(self):
        self.assertEqual(self.bid.auction, self.auction)
        self.assertEqual(self.bid.bidder, self.bidder)
        self.assertEqual(self.bid.amount, Decimal('150.00'))

    def test_bid_str(self):
        expected = '150.00 on Test Auction by bidder'
        self.assertEqual(str(self.bid), expected)


class PaymentModelTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.buyer = User.objects.create_user(
            username='buyer',
            password='testpass123'
        )
        self.auction = AuctionItem.objects.create(
            title='Test Auction',
            description='A test auction item',
            seller=self.seller,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )
        self.payment = Payment.objects.create(
            auction=self.auction,
            buyer=self.buyer,
            amount=Decimal('150.00'),
            status='pending'
        )

    def test_payment_creation(self):
        self.assertEqual(self.payment.auction, self.auction)
        self.assertEqual(self.payment.buyer, self.buyer)
        self.assertEqual(self.payment.amount, Decimal('150.00'))
        self.assertEqual(self.payment.status, 'pending')

    def test_payment_str(self):
        expected = 'Payment for Test Auction - pending'
        self.assertEqual(str(self.payment), expected)


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        # Active auction
        self.active_auction = AuctionItem.objects.create(
            title='Active Auction',
            description='An active auction',
            seller=self.user,
            category=self.category,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )
        # Ended auction
        self.ended_auction = AuctionItem.objects.create(
            title='Ended Auction',
            description='An ended auction',
            seller=self.user,
            starting_price=Decimal('50.00'),
            end_time=timezone.now() - timedelta(days=1)
        )

    def test_index_view_status_code(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_view_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'auctions/index.html')

    def test_index_shows_active_auctions(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Active Auction')
        self.assertNotContains(response, 'Ended Auction')

    def test_index_search_functionality(self):
        response = self.client.get(reverse('index'), {'q': 'Active'})
        self.assertContains(response, 'Active Auction')

    def test_index_category_filter(self):
        response = self.client.get(reverse('index'), {'category': 'electronics'})
        self.assertContains(response, 'Active Auction')


class AuctionDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.bidder = User.objects.create_user(
            username='bidder',
            password='testpass123'
        )
        self.auction = AuctionItem.objects.create(
            title='Test Auction',
            description='A test auction',
            seller=self.seller,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )

    def test_auction_detail_status_code(self):
        response = self.client.get(reverse('auction_detail', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 200)

    def test_auction_detail_template(self):
        response = self.client.get(reverse('auction_detail', args=[self.auction.pk]))
        self.assertTemplateUsed(response, 'auctions/auction_detail.html')

    def test_auction_detail_content(self):
        response = self.client.get(reverse('auction_detail', args=[self.auction.pk]))
        self.assertContains(response, 'Test Auction')
        self.assertContains(response, '100.00')

    def test_bid_requires_login(self):
        response = self.client.post(
            reverse('auction_detail', args=[self.auction.pk]),
            {'amount': '150.00'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_valid_bid(self):
        self.client.login(username='bidder', password='testpass123')
        response = self.client.post(
            reverse('auction_detail', args=[self.auction.pk]),
            {'amount': '150.00'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful bid
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, Decimal('150.00'))

    def test_invalid_bid_lower_than_current(self):
        self.client.login(username='bidder', password='testpass123')
        response = self.client.post(
            reverse('auction_detail', args=[self.auction.pk]),
            {'amount': '50.00'}
        )
        self.assertEqual(response.status_code, 200)  # Form error, stays on page
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, Decimal('100.00'))

    def test_seller_cannot_bid_on_own_auction(self):
        self.client.login(username='seller', password='testpass123')
        response = self.client.post(
            reverse('auction_detail', args=[self.auction.pk]),
            {'amount': '150.00'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect with error message
        self.assertEqual(Bid.objects.count(), 0)


class CreateAuctionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='seller',
            password='testpass123'
        )

    def test_create_auction_requires_login(self):
        response = self.client.get(reverse('create_auction'))
        self.assertEqual(response.status_code, 302)

    def test_create_auction_view_logged_in(self):
        self.client.login(username='seller', password='testpass123')
        response = self.client.get(reverse('create_auction'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions/create_auction.html')

    def test_create_auction_success(self):
        self.client.login(username='seller', password='testpass123')
        end_time = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('create_auction'), {
            'title': 'New Auction',
            'description': 'A new auction',
            'starting_price': '200.00',
            'end_time': end_time,
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(AuctionItem.objects.filter(title='New Auction').exists())


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.auction = AuctionItem.objects.create(
            title='My Auction',
            description='My test auction',
            seller=self.user,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_view_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions/dashboard.html')

    def test_dashboard_shows_user_auctions(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'My Auction')


class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_view_logged_in(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions/profile.html')

    def test_profile_update(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('profile'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newemail@example.com',
            'display_name': 'TestDisplay',
            'country': 'UK',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_view_status_code(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_view_template(self):
        response = self.client.get(reverse('register'))
        self.assertTemplateUsed(response, 'auctions/register.html')

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Check that profile was created
        user = User.objects.get(username='newuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_login_view_status_code(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success


class CategoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

    def test_category_list_view(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions/category_list.html')
        self.assertContains(response, 'Electronics')

    def test_category_detail_view(self):
        response = self.client.get(reverse('category_detail', args=['electronics']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auctions/category_detail.html')


class EditDeleteAuctionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = User.objects.create_user(
            username='seller',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        self.auction = AuctionItem.objects.create(
            title='Test Auction',
            description='A test auction',
            seller=self.seller,
            starting_price=Decimal('100.00'),
            end_time=timezone.now() + timedelta(days=7)
        )

    def test_edit_auction_requires_login(self):
        response = self.client.get(reverse('edit_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 302)

    def test_edit_auction_requires_owner(self):
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('edit_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 404)

    def test_edit_auction_owner_access(self):
        self.client.login(username='seller', password='testpass123')
        response = self.client.get(reverse('edit_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_auction_requires_owner(self):
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('delete_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_auction_owner_access(self):
        self.client.login(username='seller', password='testpass123')
        response = self.client.get(reverse('delete_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 200)

    def test_cannot_edit_auction_with_bids(self):
        bidder = User.objects.create_user(username='bidder', password='testpass123')
        Bid.objects.create(auction=self.auction, bidder=bidder, amount=Decimal('150.00'))
        self.client.login(username='seller', password='testpass123')
        response = self.client.get(reverse('edit_auction', args=[self.auction.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect with error
