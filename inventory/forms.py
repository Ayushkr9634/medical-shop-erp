from django import forms
from .models import Medicine,EmailSettings
from .models import Supplier
from django.contrib.auth.password_validation import validate_password
from .models import Purchase
from .models import PurchaseItem
from .models import Sale, UserProfile
from datetime import date
from .models import SaleItem
from .models import ShopSettings
from .models import StockReduction
from django.contrib.auth.models import (User,Group)
from django.contrib.auth.forms import UserCreationForm
class CustomUserCreationForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        required=True
    )

    last_name = forms.CharField(
        max_length=150,
        required=False
    )

    email = forms.EmailField(
        required=True
    )

    mobile_number = forms.CharField(
        max_length=10,
        required=True
    )

    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows":3
            }
        ),
        required=False
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label="Select Role"
    )

    class Meta:

        model = User

        fields = (

            "username",

            "first_name",

            "last_name",

            "email",

            "password1",

            "password2"

        )

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "This email address is already registered."
            )

        return email

    def clean_mobile_number(self):

        mobile = self.cleaned_data["mobile_number"].strip()

        if len(mobile) != 10:

            raise forms.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        if not mobile.isdigit():

            raise forms.ValidationError(
                "Mobile number must contain digits only."
            )

        if UserProfile.objects.filter(
            mobile_number=mobile
        ).exists():

            raise forms.ValidationError(
                "This mobile number already exists."
            )

        return mobile

    def save(self, commit=True):

        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]

        user.last_name = self.cleaned_data["last_name"]

        user.email = self.cleaned_data["email"].strip().lower()

        if commit:

            user.save()

        return user
class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = [
            'shop_name',
            'drug_license_number',
            'mobile',
            'gst_number',
            'email',
            'address'
        ]

class SaleItemForm(forms.ModelForm):

    class Meta:
        model = SaleItem

        fields = [
            'sale',
            'medicine',
            'quantity',
            'selling_price'
        ]

    def clean(self):

        cleaned_data = super().clean()

        medicine = cleaned_data.get(
            'medicine'
        )

        quantity = cleaned_data.get(
            'quantity'
        )

        if medicine and quantity:

            if quantity > medicine.stock_quantity:

                raise forms.ValidationError(
                    f"Only {medicine.stock_quantity} units available in stock."
                )

        return cleaned_data

class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale

        fields = [
    'customer_name',
    'customer_mobile',
    'customer_address',
    'customer_email',
    'customer_gst',
    'customer_drug_license',
    'sale_date'
]

        widgets = {
            'sale_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            )
        }
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields[
    'customer_name'
].required = True

            self.fields[
    'customer_mobile'
].required = True

            self.fields[
    'customer_address'
].required = True
            self.fields[
    'customer_name'
].widget.attrs.update({
    'required': True
})

            self.fields[
    'customer_mobile'
].widget.attrs.update({
    'required': True
})

            self.fields[
    'customer_address'
].widget.attrs.update({
    'required': True
})
            self.fields[
                'sale_date'
            ].initial = date.today()
class PurchaseItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseItem

        fields = [
            'purchase',
            'medicine',
            'quantity',
            'purchase_price'
        ]

class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase

        fields = [
    'supplier',
    'purchase_date'
]
        widgets = {
            'purchase_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            )
        }

class SupplierForm(forms.ModelForm):

    class Meta:
        model = Supplier

        fields = [
            'name',
            'gst_number',
            'phone',
            'email',
            'drug_license_number',
            'address'

        ]

class MedicineForm(forms.ModelForm):

    class Meta:
        model = Medicine

        fields = [
            'name',
            'manufacturer',
            'batch_number',
            'expiry_date',
            'purchase_price',
            'selling_price',
            'stock_quantity',
            'image',
        ]
        widgets = {
            'expiry_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            )
        }
class RestoreForm(forms.Form):

    backup_file = forms.FileField()
class StockReductionForm(forms.ModelForm):

    class Meta:

        model = StockReduction

        fields = [

            'reason',
            'quantity',

        ]
class UserEditForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=150,
        required=True
    )

    last_name = forms.CharField(
        max_length=150,
        required=False
    )

    email = forms.EmailField(
        required=True
    )

    mobile_number = forms.CharField(
        max_length=10,
        required=True
    )

    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows":3
            }
        ),
        required=False
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label=None
    )

    is_active = forms.BooleanField(
        required=False
    )

    class Meta:

        model = User

        fields = [

            "username",

            "first_name",

            "last_name",

            "email",

            "is_active"

        ]

    def clean_email(self):

        email = self.cleaned_data["email"].strip().lower()

        existing = User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        )

        if existing.exists():

            raise forms.ValidationError(
                "This email address is already registered."
            )

        return email

    def clean_mobile_number(self):

        mobile = self.cleaned_data["mobile_number"].strip()

        if not mobile.isdigit():

            raise forms.ValidationError(
                "Mobile number must contain digits only."
            )

        if len(mobile) != 10:

            raise forms.ValidationError(
                "Mobile number must be exactly 10 digits."
            )

        profile = UserProfile.objects.filter(
            mobile_number=mobile
        ).exclude(
            user=self.instance
        )

        if profile.exists():

            raise forms.ValidationError(
                "This mobile number already exists."
            )

        return mobile

    def save(self, commit=True):

        user = super().save(commit=False)

        user.email = self.cleaned_data["email"].strip().lower()

        if commit:

            user.save()

        return user
class ForgotUsernameForm(forms.Form):

    email = forms.EmailField(
        required=False,
        label="Registered Email"
    )

    mobile_number = forms.CharField(
        max_length=10,
        required=False,
        label="Registered Mobile Number"
    )

    def clean(self):

        cleaned_data = super().clean()

        email = cleaned_data.get("email")

        mobile = cleaned_data.get("mobile_number")

        if not email and not mobile:

            raise forms.ValidationError(
                "Enter either Email or Mobile Number."
            )

        return cleaned_data


class ForgotPasswordForm(forms.Form):

    email = forms.EmailField(

        label="Registered Email",

        widget=forms.EmailInput(

            attrs={

                "placeholder":"Enter your registered email"

            }

        )

    )


class OTPVerificationForm(forms.Form):

    otp = forms.CharField(
        max_length=6,
        min_length=6,
        label="OTP",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter 6-digit OTP"
            }
        )
    )


class ResetPasswordForm(forms.Form):

    password1 = forms.CharField(
    label="New Password",
    widget=forms.PasswordInput()
)

    password2 = forms.CharField(
    label="Confirm Password",
    widget=forms.PasswordInput()
)

    def clean(self):

        cleaned_data = super().clean()

        p1 = cleaned_data.get("password1")

        p2 = cleaned_data.get("password2")

        if p1 != p2:

            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data
class EmailSettingsForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            render_value=True
        )
    )

    class Meta:

        model = EmailSettings

        fields = [

            "provider",

            "smtp_host",

            "smtp_port",

            "username",

            "password",

            "sender_name",

            "sender_email",

            "use_tls",

            "use_ssl",

            "is_active"

        ]

        widgets = {

            "provider": forms.Select(),

            "smtp_port": forms.NumberInput(),

        }
class ForgotUsernameForm(forms.Form):

    email = forms.EmailField(

        label="Registered Email",

        widget=forms.EmailInput(

            attrs={

                "placeholder": "Enter your registered email"

            }

        )

    )
class ChangeMyPasswordForm(forms.Form):

    current_password = forms.CharField(

        label="Current Password",

        widget=forms.PasswordInput()

    )

    new_password = forms.CharField(

        label="New Password",

        widget=forms.PasswordInput()

    )

    confirm_password = forms.CharField(

        label="Confirm Password",

        widget=forms.PasswordInput()

    )

    def __init__(self, user, *args, **kwargs):

        self.user = user

        super().__init__(*args, **kwargs)

    def clean_current_password(self):

        password = self.cleaned_data["current_password"]

        if not self.user.check_password(password):

            raise forms.ValidationError(

                "Current password is incorrect."

            )

        return password

    def clean(self):

        cleaned_data = super().clean()

        new_password = cleaned_data.get("new_password")

        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:

            raise forms.ValidationError(

                "Passwords do not match."

            )

        if new_password:

            validate_password(

                new_password,

                self.user

            )

        return cleaned_data
class SetupForm(forms.Form):

    shop_name = forms.CharField(
        max_length=200
    )

    owner_first_name = forms.CharField(
    max_length=150,
    label="Owner First Name"
)

    owner_last_name = forms.CharField(
    max_length=150,
    label="Owner Last Name"
)

    email = forms.EmailField()

    mobile = forms.CharField(
        max_length=10
    )

    username = forms.CharField(
        max_length=150
    )

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
    )

    def clean_email(self):

        email = self.cleaned_data["email"].lower()

        if User.objects.filter(
            email=email
        ).exists():

            raise forms.ValidationError(
                "Email already exists."
            )

        return email

    def clean_username(self):

        username = self.cleaned_data["username"]

        if User.objects.filter(
            username=username
        ).exists():

            raise forms.ValidationError(
                "Username already exists."
            )

        return username

    def clean_mobile(self):

        mobile = self.cleaned_data["mobile"]

        if len(mobile) != 10:

            raise forms.ValidationError(
                "Enter a valid mobile number."
            )

        if not mobile.isdigit():

            raise forms.ValidationError(
                "Only digits are allowed."
            )

        return mobile

    def clean(self):

        cleaned = super().clean()

        if cleaned.get("password") != cleaned.get("confirm_password"):

            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned


class SetupOTPForm(forms.Form):

    otp = forms.CharField(
        max_length=6
    )