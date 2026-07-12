from django.db import models
from datetime import date
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
class PasswordResetOTP(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_used = models.BooleanField(
        default=False
    )

    def save(self, *args, **kwargs):

        if not self.expires_at:

            self.expires_at = timezone.now() + timedelta(minutes=10)

        super().save(*args, **kwargs)

    def is_expired(self):

        if self.expires_at is None:
            return False

        return timezone.now() > self.expires_at

    def __str__(self):

        return f"{self.user.username} - {self.otp}"
class Medicine(models.Model):
    LOW_STOCK_THRESHOLD = 20
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    batch_number = models.CharField(max_length=100, unique=True)
    expiry_date = models.DateField()
    
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    # Added to track when the inventory record is modified
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['name'] # Orders querysets by name alphabetically

    def __str__(self):
        return f"{self.name} (Batch: {self.batch_number})"
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.LOW_STOCK_THRESHOLD
    @property
    def days_until_expiry(self):
        return (
            self.expiry_date - date.today()
    ).days
    @property
    def is_expiring_soon(self):
        return (
            0 <= self.days_until_expiry <= 30
    )
    @property
    def profit_per_unit(self):
        return (
        self.selling_price -
        self.purchase_price
    )
    @property
    def is_expired(self):
        """Returns True if the medicine is past its expiry date."""
        return date.today() > self.expiry_date

    @property
    def is_in_stock(self):
        """Returns True if there is stock available."""
        return self.stock_quantity > 0
class Supplier(models.Model):
    name = models.CharField(
    max_length=200
)

    gst_number = models.CharField(
    max_length=50,
    blank=True
)

    drug_license_number = models.CharField(
    max_length=100,
    blank=True
)

    phone = models.CharField(
    max_length=20,
    blank=True
)

    email = models.EmailField(
    blank=True
)

    address = models.TextField(
    blank=True
)

    created_at = models.DateTimeField(
    auto_now_add=True
)

def __str__(self):

    return self.name


class Purchase(models.Model):

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT
    )

    invoice_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    purchase_date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.invoice_number:

            last_purchase = Purchase.objects.order_by(
                '-id'
            ).first()

            if (
                last_purchase and
                last_purchase.invoice_number.startswith('PUR-')
            ):

                last_number = int(
                    last_purchase.invoice_number.replace(
                        'PUR-',
                        ''
                    )
                )

                new_number = last_number + 1

            else:

                new_number = 1

            self.invoice_number = (
                f'PUR-{new_number:05d}'
            )

        super().save(*args, **kwargs)
    @property
    def total_amount(self):

        return sum(
        item.quantity * item.purchase_price
        for item in self.items.all()
    )
    def __str__(self):

        return self.invoice_number
class PurchaseItem(models.Model):
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:

            StockTransaction.objects.create(
                medicine=self.medicine,
                transaction_type='PURCHASE',
                quantity=self.quantity,
                notes=f"Purchase Invoice {self.purchase.invoice_number}"
            )

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items'
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return (
            f"{self.purchase.invoice_number} - "
            f"{self.medicine.name}"
        )
class Sale(models.Model):

    invoice_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    sale_date = models.DateField()

    customer_name = models.CharField(
    max_length=200
)

    customer_mobile = models.CharField(
    max_length=15
)

    customer_address = models.TextField()

    customer_email = models.EmailField(
    blank=True
)

    customer_gst = models.CharField(
    max_length=50,
    blank=True
)

    customer_drug_license = models.CharField(
    max_length=100,
    blank=True
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def total_amount(self):

        return sum(
            item.quantity * item.selling_price
            for item in self.items.all()
        )

    def save(self, *args, **kwargs):

        if not self.invoice_number:

            last_sale = Sale.objects.order_by(
                '-id'
            ).first()

            if (
                last_sale and
                last_sale.invoice_number.startswith('SALE-')
            ):

                last_number = int(
                    last_sale.invoice_number.replace(
                        'SALE-',
                        ''
                    )
                )

                new_number = last_number + 1

            else:

                new_number = 1

            self.invoice_number = (
                f'SALE-{new_number:05d}'
            )

        super().save(*args, **kwargs)

    def __str__(self):

        return self.invoice_number
class SaleItem(models.Model):
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        if is_new:

            if self.quantity > self.medicine.stock_quantity:
                raise ValueError(
                    f"Not enough stock for {self.medicine.name}"
                )

        super().save(*args, **kwargs)

        if is_new:

            StockTransaction.objects.create(
                medicine=self.medicine,
                transaction_type='SALE',
                quantity=self.quantity,
                notes=f"Sale Invoice {self.sale.invoice_number}"
            )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    @property
    def line_total(self):

        return (
        self.quantity *
        self.selling_price
    )
    def __str__(self):
        return (
            f"{self.sale.invoice_number} - "
            f"{self.medicine.name}"
        )
class StockTransaction(models.Model):

    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('DAMAGED', 'Damaged'),
        ('EXPIRED', 'Expired'),
        ('LOST', 'Lost'),
    ]

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    quantity = models.IntegerField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            if self.transaction_type in [
                'PURCHASE',
                'RETURN'
            ]:
                self.medicine.stock_quantity += self.quantity

            elif self.transaction_type in [
                'SALE',
                'DAMAGED',
                'EXPIRED'
            ]:
                self.medicine.stock_quantity -= self.quantity

            self.medicine.save()

    def __str__(self):
        return (
            f"{self.medicine.name} - "
            f"{self.transaction_type} - "
            f"{self.quantity}"
        )
class ShopSettings(models.Model):

    shop_name = models.CharField(
        max_length=200
    )

    drug_license_number = models.CharField(
        max_length=100
    )
    gst_number = models.CharField(
max_length=50,
blank=True
)

    mobile = models.CharField(
        max_length=20
    )

    email = models.EmailField()

    address = models.TextField()

    def __str__(self):

        return self.shop_name
class ActivityLog(models.Model):

    user = models.CharField(
        max_length=100
    )

    action = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return (
            f"{self.user} - {self.action}"
        )
class StockReduction(models.Model):

    REASONS = [

        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
        ('LOST', 'Lost'),

    ]

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()

    reason = models.CharField(
        max_length=20,
        choices=REASONS
    )

    previous_stock = models.PositiveIntegerField()

    new_stock = models.PositiveIntegerField()

    adjusted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    mobile_number = models.CharField(
        max_length=10,
        unique=True
    )

    address = models.TextField(
        blank=True
    )


    is_online = models.BooleanField(
        default=False
    )

    last_seen = models.DateTimeField(
        blank=True,
        null=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.user.username
class EmailSettings(models.Model):

    PROVIDERS = [

        ("CUSTOM", "Custom SMTP"),

        ("GMAIL", "Gmail"),

        ("OUTLOOK", "Outlook"),

        ("ZOHO", "Zoho"),

        ("OFFICE365", "Office 365"),

    ]

    provider = models.CharField(
        max_length=20,
        choices=PROVIDERS,
        default="CUSTOM"
    )

    smtp_host = models.CharField(
        max_length=200
    )

    smtp_port = models.PositiveIntegerField(
        default=587
    )

    username = models.EmailField()

    password = models.CharField(
        max_length=255
    )

    sender_name = models.CharField(
        max_length=200
    )

    sender_email = models.EmailField()

    use_tls = models.BooleanField(
        default=True
    )

    use_ssl = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "Email Configuration"

        verbose_name_plural = "Email Configuration"

    def __str__(self):

        return self.sender_email
class EmailTemplate(models.Model):

    TEMPLATE_TYPES = [

        ("OTP", "Password OTP"),

        ("USERNAME", "Username Recovery"),

        ("WELCOME", "Welcome Email"),

        ("LOW_STOCK", "Low Stock"),

        ("EXPIRY", "Expiry Alert"),

    ]

    template_type = models.CharField(
        max_length=30,
        unique=True,
        choices=TEMPLATE_TYPES
    )

    subject = models.CharField(
        max_length=255
    )

    body = models.TextField()

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.template_type
class EmailLog(models.Model):

    STATUS = [

        ("SUCCESS","Success"),

        ("FAILED","Failed")

    ]

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=255
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS
    )

    error = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.recipient


    def __str__(self):

        return f"{self.user.username} - {self.otp}"

class InstallationStatus(models.Model):

    is_completed = models.BooleanField(
        default=False
    )

    shop_name = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    owner_name = models.CharField(
        max_length=200,
        blank=True,
        default=""
    )

    owner_email = models.EmailField(
        blank=True,
        default=""
    )

    installed_on = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    current_version = models.CharField(
        max_length=20,
        default="1.0"
    )

    def __str__(self):
        return self.shop_name or "Medical Shop ERP"

class SetupOTP(models.Model):

    email = models.EmailField(
        unique=True
    )

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveIntegerField(
        default=0
    )

    is_verified = models.BooleanField(
        default=False
    )

    @staticmethod
    def generate():

        return str(

            random.randint(

                100000,

                999999

            )

        )

    @staticmethod
    def expiry():

        return timezone.now() + timedelta(
            minutes=5
        )

    def expired(self):

        return timezone.now() > self.expires_at