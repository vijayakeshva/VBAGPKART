from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def _create_user(self, email, password=None, phone_number=None, **extra_fields):
        """
        Creates and saves a user with the given email and password.
        """
        if not email:
            raise ValueError(_('Users must have an email address'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, phone_number=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, phone_number, **extra_fields)

    def create_superuser(self, email, password=None, phone_number=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, phone_number, **extra_fields)

    def get_with_profile(self, **kwargs):
        """Get user with related profile in a single query"""
        return self.select_related(
            'platform_user',
            'buyer_user'
        ).get(**kwargs)
    

    def filter_with_profiles(self, **kwargs):
        """Filter users with related profiles in a single query"""
        return self.select_related(
            'platform_user',
            'buyer_user'
        ).filter(**kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that supports using email or phone number as the primary identifier.
    """
    class UserType(models.TextChoices):
        PLATFORM = 'PLATFORM', _('Platform User') 
        BUYER = 'BUYER', _('Buyer')     
        UNASSIGNED = 'UNASSIGNED', _('Unassigned') 

    class Gender(models.TextChoices):
        MALE = 'MALE', _('Male')
        FEMALE = 'FEMALE', _('Female')
        OTHER = 'OTHER', _('Other')
        PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY', _('Prefer not to say')

    # Core authentication fields
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. A valid email address for the user.'),
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Phone number in international format (e.g. +919876543210)'),
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
            )
        ],
        error_messages={
            'unique': _("A user with that phone number already exists."),
        }
    )
    
    # User type and permissions
    user_type = models.CharField(
        _('user type'),
        max_length=10,
        choices=UserType.choices,
        default=UserType.UNASSIGNED,
        help_text=_('Designates the type of user account')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    
    # Personal info
    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=True,
        help_text=_('The user\'s first name')
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=True,
        help_text=_('The user\'s last name')
    )
    gender = models.CharField(
        _('gender'),
        max_length=20,
        choices=Gender.choices,
        blank=True,
        null=True,
        help_text=_('The gender with which the user identifies')
    )
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
        help_text=_('The user\'s date of birth in YYYY-MM-DD format')
    )
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='user_profiles/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_('A profile picture for the user')
    )
    
    # Verification and metadata
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user\'s email has been verified.')
    )
    phone_verified = models.BooleanField(
        _('phone verified'),
        default=False,
        help_text=_('Designates whether this user\'s phone number has been verified.')
    )
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now,
        help_text=_('The date when the user account was created')
    )
    last_login = models.DateTimeField(
        _('last login'),
        blank=True,
        null=True,
        help_text=_('The last time this user logged in')
    )
    last_updated = models.DateTimeField(
        _('last updated'),
        auto_now=True,
        help_text=_('The last time this user\'s information was updated')
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
            models.Index(fields=['last_name', 'first_name']),
        ]

    def __str__(self):
        return self.get_display_name()

    def clean(self):
        super().clean()
        if not (self.email or self.phone_number):
            raise ValidationError(_('At least one of email or phone number must be provided.'))
        
        # Validate profile relationships based on user type
        type_profile_map = {
            self.UserType.PLATFORM: 'platform_user',
            self.UserType.BUYER: 'buyer_user'
        }

        if self.user_type in type_profile_map:
            profile_attr = type_profile_map[self.user_type]
            if not hasattr(self, profile_attr):
                raise ValidationError(_(f'Users with type {self.user_type} must have a {profile_attr}.'))
        elif self.user_type == self.UserType.UNASSIGNED:
            if any(hasattr(self, attr) for attr in type_profile_map.values()):
                raise ValidationError(_('Unassigned users must not have any profile.'))

    def get_display_name(self):
        """
        Returns the best available display name for the user.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        elif self.email:
            return self.email.split('@')[0]
        elif self.phone_number:
            return self.phone_number
        return f"User #{self.id}"

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def get_short_name(self):
        """Return the short name for the user (first name or email prefix)."""
        return self.first_name or self.email.split('@')[0]

    def get_profile(self):
        """Get the appropriate profile based on user type."""
        if self.user_type == self.UserType.PLATFORM and hasattr(self, 'platform_user'):
            return self.platform_user
        elif self.user_type == self.UserType.BUYER and hasattr(self, 'buyer_user'):
            return self.buyer_user
        return None


class PlatformUser(models.Model):
    
    """
    Extended profile for platform staff users with role-based permissions.
    """
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', _('Super Administrator')
        ADMIN = 'ADMIN', _('Administrator')
        PRODUCT_MANAGER = 'PRODUCT_MANAGER', _('Product Manager')
        INVENTORY_MANAGER = 'INVENTORY_MANAGER', _('Inventory Manager')
        CUSTOMER_SUPPORT = 'CUSTOMER_SUPPORT', _('Customer Support')
        MARKETING = 'MARKETING', _('Marketing Specialist')
        SALES = 'SALES', _('Sales Representative')
        ANALYST = 'ANALYST', _('Business Analyst')
        CONTENT_MANAGER = 'CONTENT_MANAGER', _('Content Manager')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='platform_user',
        verbose_name=_('user account')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text=_('The staff member\'s primary role in the organization')
    )
    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('The department to which this staff member belongs')
    )
    employee_id = models.CharField(
        _('employee ID'),
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text=_('The official employee identification number')
    )
    hire_date = models.DateField(
        _('hire date'),
        default=timezone.now,
        help_text=_('The date when this staff member was hired')
    )
    is_management = models.BooleanField(
        _('management role'),
        default=False,
        help_text=_('Designates whether this staff member has management responsibilities')
    )
    
    # Permission flags (more granular than Django's built-in permissions)
    can_manage_users = models.BooleanField(
        _('can manage users'),
        default=False,
        help_text=_('Designates whether this staff can manage user accounts')
    )
    can_manage_products = models.BooleanField(
        _('can manage products'),
        default=False,
        help_text=_('Designates whether this staff can manage product catalog')
    )
    can_manage_orders = models.BooleanField(
        _('can manage orders'),
        default=False,
        help_text=_('Designates whether this staff can manage customer orders')
    )
    can_manage_content = models.BooleanField(
        _('can manage content'),
        default=False,
        help_text=_('Designates whether this staff can manage website content')
    )
    can_view_reports = models.BooleanField(
        _('can view reports'),
        default=False,
        help_text=_('Designates whether this staff can view business reports')
    )
    
    # Additional metadata
    bio = models.TextField(
        _('biography'),
        blank=True,
        null=True,
        help_text=_('A short biography or description of the staff member')
    )
    profile_completed = models.BooleanField(
        _('profile completed'),
        default=False,
        help_text=_('Designates whether this staff profile is fully completed')
    )
    last_promotion_date = models.DateField(
        _('last promotion date'),
        blank=True,
        null=True,
        help_text=_('The date when this staff member was last promoted')
    )
    notes = models.TextField(
        _('internal notes'),
        blank=True,
        null=True,
        help_text=_('Internal notes about this staff member')
    )

    class Meta:
        verbose_name = _('platform user')
        verbose_name_plural = _('platform users')
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['department']),
            models.Index(fields=['is_management']),
        ]

    def __str__(self):
        return f"{self.user.get_display_name()} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Ensure the user type is set to PLATFORM
        if self.user.user_type != User.UserType.PLATFORM:
            self.user.user_type = User.UserType.PLATFORM
            self.user.save(update_fields=['user_type'])
        super().save(*args, **kwargs)

    def is_super_admin(self):
        """Check if this staff member is a super administrator."""
        return self.role == self.Role.SUPER_ADMIN

    def get_permissions(self):
        """Return a list of permission strings this staff member has."""
        permissions = []
        if self.can_manage_users:
            permissions.append('manage_users')
        if self.can_manage_products:
            permissions.append('manage_products')
        if self.can_manage_orders:
            permissions.append('manage_orders')
        if self.can_manage_content:
            permissions.append('manage_content')
        if self.can_view_reports:
            permissions.append('view_reports')
        return permissions


class BuyerUser(models.Model):
    """
    Extended profile for buyer/customer accounts with purchase history and preferences.
    """
    class Tier(models.TextChoices):
        STANDARD = 'STANDARD', _('Standard')
        SILVER = 'SILVER', _('Silver')
        GOLD = 'GOLD', _('Gold')
        PLATINUM = 'PLATINUM', _('Platinum')
        VIP = 'VIP', _('VIP')

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')
        BLACKLISTED = 'BLACKLISTED', _('Blacklisted')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='buyer_user',
        verbose_name=_('user account')
    )
    tier = models.CharField(
        _('tier'),
        max_length=10,
        choices=Tier.choices,
        default=Tier.STANDARD,
        help_text=_('The buyer\'s loyalty program tier level')
    )
    status = models.CharField(
        _('status'),
        max_length=15,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('The current status of this buyer account')
    )
    
    # Purchase history metrics
    lifetime_value = models.DecimalField(
        _('lifetime value'),
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_('Total amount spent by this buyer across all orders')
    )
    average_order_value = models.DecimalField(
        _('average order value'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('The average amount spent per order by this buyer')
    )
    order_count = models.PositiveIntegerField(
        _('order count'),
        default=0,
        help_text=_('Total number of orders placed by this buyer')
    )
    last_order_date = models.DateTimeField(
        _('last order date'),
        blank=True,
        null=True,
        help_text=_('The date when this buyer last placed an order')
    )
    first_order_date = models.DateTimeField(
        _('first order date'),
        blank=True,
        null=True,
        help_text=_('The date when this buyer placed their first order')
    )
    
    # Loyalty program
    loyalty_points = models.PositiveIntegerField(
        _('loyalty points'),
        default=0,
        help_text=_('Current balance of loyalty points')
    )
    loyalty_points_earned = models.PositiveIntegerField(
        _('lifetime loyalty points earned'),
        default=0,
        help_text=_('Total loyalty points ever earned by this buyer')
    )
    loyalty_points_redeemed = models.PositiveIntegerField(
        _('loyalty points redeemed'),
        default=0,
        help_text=_('Total loyalty points redeemed by this buyer')
    )
    
    # Preferences
    preferred_payment_method = models.CharField(
        _('preferred payment method'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('The buyer\'s preferred payment method')
    )
    preferred_shipping_method = models.CharField(
        _('preferred shipping method'),
        max_length=50,
        blank=True,
        null=True,
        help_text=_('The buyer\'s preferred shipping method')
    )
    preferred_communication_channel = models.CharField(
        _('preferred communication channel'),
        max_length=20,
        choices=(
            ('EMAIL', _('Email')),
            ('SMS', _('SMS')),
            ('APP', _('Mobile App')),
            ('WHATSAPP', _('WhatsApp'))
        ),
        default='EMAIL',
        help_text=_('The buyer\'s preferred channel for communications')
    )
    
    # Marketing preferences
    newsletter_subscription = models.BooleanField(
        _('newsletter subscription'),
        default=True,
        help_text=_('Designates whether this buyer is subscribed to newsletters')
    )
    marketing_opt_in = models.BooleanField(
        _('marketing opt-in'),
        default=False,
        help_text=_('Designates whether this buyer has opted in to marketing communications')
    )
    personalized_ads_opt_in = models.BooleanField(
        _('personalized ads opt-in'),
        default=False,
        help_text=_('Designates whether this buyer has opted in to personalized advertising')
    )
    
    # Account metadata
    account_balance = models.DecimalField(
        _('account balance'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('Current balance in the buyer\'s wallet or account credit')
    )
    referral_code = models.CharField(
        _('referral code'),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Unique code this buyer can share for referrals')
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_('The buyer who referred this account')
    )
    notes = models.TextField(
        _('internal notes'),
        blank=True,
        null=True,
        help_text=_('Internal notes about this buyer')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When this buyer profile was created')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When this buyer profile was last updated')
    )

    class Meta:
        verbose_name = _('buyer user')
        verbose_name_plural = _('buyer users')
        ordering = ['-lifetime_value']
        indexes = [
            models.Index(fields=['tier']),
            models.Index(fields=['status']),
            models.Index(fields=['lifetime_value']),
            models.Index(fields=['last_order_date']),
            models.Index(fields=['referral_code']),
        ]

    def __str__(self):
        return f"{self.user.get_display_name()} ({self.get_tier_display()} Buyer)"

    def save(self, *args, **kwargs):
        # Ensure the user type is set to BUYER
        if self.user.user_type != User.UserType.BUYER:
            self.user.user_type = User.UserType.BUYER
            self.user.save(update_fields=['user_type'])
        
        # Generate referral code if not set
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        """Generate a unique referral code for this buyer."""
        from django.utils.crypto import get_random_string
        code = get_random_string(8).upper()
        while BuyerUser.objects.filter(referral_code=code).exists():
            code = get_random_string(8).upper()
        return code

    def update_tier(self):
        """Automatically update buyer tier based on lifetime value."""
        if self.lifetime_value >= 50000:
            self.tier = self.Tier.VIP
        elif self.lifetime_value >= 20000:
            self.tier = self.Tier.PLATINUM
        elif self.lifetime_value >= 10000:
            self.tier = self.Tier.GOLD
        elif self.lifetime_value >= 5000:
            self.tier = self.Tier.SILVER
        else:
            self.tier = self.Tier.STANDARD
        self.save()

    def add_loyalty_points(self, points, reason=""):
        """Add loyalty points to the buyer's account with an optional reason."""
        self.loyalty_points += points
        self.loyalty_points_earned += points
        self.save()
        return self.loyalty_points


class Address(models.Model):
    """
    Address model for storing buyer shipping and billing addresses.
    """
    class AddressType(models.TextChoices):
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        BILLING = 'BILLING', _('Billing')
        SHIPPING = 'SHIPPING', _('Shipping')
        OTHER = 'OTHER', _('Other')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user account'),
        help_text=_('The user to whom this address belongs')
    )
    address_type = models.CharField(
        _('address type'),
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME,
        help_text=_('The type of address (home, work, etc.)')
    )
    is_default = models.BooleanField(
        _('default address'),
        default=False,
        help_text=_('Designates whether this is the default address for its type')
    )
    
    # Contact information
    full_name = models.CharField(
        _('full name'),
        max_length=255,
        help_text=_('The full name of the person at this address')
    )
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
            )
        ],
        help_text=_('A contact phone number for this address')
    )
    company = models.CharField(
        _('company'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Company name if this is a business address')
    )
    
    # Address components
    address_line_1 = models.CharField(
        _('address line 1'),
        max_length=255,
        help_text=_('The primary street address or PO box')
    )
    address_line_2 = models.CharField(
        _('address line 2'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Apartment, suite, unit, building, floor, etc.')
    )
    landmark = models.CharField(
        _('landmark'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('A nearby landmark to help locate the address')
    )
    city = models.CharField(
        _('city'),
        max_length=100,
        help_text=_('The city or locality')
    )
    state = models.CharField(
        _('state/province/region'),
        max_length=100,
        help_text=_('The state, province, or region')
    )
    postal_code = models.CharField(
        _('postal code'),
        max_length=20,
        help_text=_('The postal code or ZIP code')
    )
    country = models.CharField(
        _('country'),
        max_length=100,
        default='India',
        help_text=_('The country')
    )
    
    # Additional metadata
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this address is currently in use')
    )
    notes = models.TextField(
        _('delivery notes'),
        blank=True,
        null=True,
        help_text=_('Special instructions for delivery to this address')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When this address was created')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When this address was last updated')
    )

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', 'address_type', 'city']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['city']),
            models.Index(fields=['state']),
            models.Index(fields=['postal_code']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.full_name}, {self.address_line_1}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure no other address of the same type is marked as default
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def get_formatted_address(self):
        """Return a properly formatted address string."""
        lines = []
        if self.company:
            lines.append(self.company)
        lines.append(self.address_line_1)
        if self.address_line_2:
            lines.append(self.address_line_2)
        if self.landmark:
            lines.append(_("Near: ") + self.landmark)
        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country)
        return "\n".join(lines)