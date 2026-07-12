from .services import send_email, InstallationService
import random
from .models import InstallationStatus
from .forms import SetupForm
from django.utils import timezone
from .models import (
    SetupOTP,
    InstallationStatus,
    ShopSettings,
    UserProfile,
)
from .models import PasswordResetOTP
from django.conf import settings
from .models import UserProfile
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from datetime import datetime,timedelta
from django.core.management import call_command
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import (
    User,
    Group
)
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import UserProfile,EmailSettings,SetupOTP
from .forms import (
    ForgotUsernameForm,
    ForgotPasswordForm,
    OTPVerificationForm,
    ResetPasswordForm,EmailSettingsForm,
    SetupForm,SetupOTPForm
)
from functools import wraps
from .forms import UserEditForm
from .services import send_email
from django.contrib.auth.hashers import make_password

def reset_password(request):

    if not request.session.get("otp_verified"):

        messages.error(

            request,

            "Please verify your OTP first."

        )

        return redirect("forgot_password")

    email = request.session.get("reset_email")

    if not email:

        messages.error(

            request,

            "Password reset session expired."

        )

        return redirect("forgot_password")

    user = User.objects.filter(

        email__iexact=email

    ).first()

    if not user:

        messages.error(

            request,

            "Invalid request."

        )

        return redirect("forgot_password")

    form = ResetPasswordForm()

    if request.method == "POST":

        form = ResetPasswordForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data["password1"]

            user.password = make_password(password)

            user.save()

            PasswordResetOTP.objects.filter(

                user=user

            ).delete()

            request.session.pop(

                "otp_verified",

                None

            )

            request.session.pop(

                "reset_email",

                None

            )

            ActivityLog.objects.create(

                user=user.username,

                action="Password Reset Successfully"

            )

            messages.success(

                request,

                "Password changed successfully. Please login."

            )

            return redirect("login")

    return render(

        request,

        "registration/reset_password.html",

        {

            "form": form

        }

    )

def forgot_username(request):

    form = ForgotUsernameForm()

    if request.method == "POST":

        form = ForgotUsernameForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"].strip().lower()

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user:

                subject = "Medical Shop ERP - Username Recovery"

                message = f"""
Hello {user.first_name or user.username},

You requested your username.

Your username is:

{user.username}

If you did not request this email, please ignore it.

Regards,
Medical Shop ERP
"""

                send_email(

                    recipient=email,

                    subject=subject,

                    message=message

                )

            messages.success(

                request,

                "If an account exists with this email, your username has been sent."

            )

            return redirect("login")

    return render(

        request,

        "registration/forgot_username.html",

        {

            "form": form

        }

    )
def admin_required(view_func):

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        if not is_admin(request.user):

            return redirect(
                'dashboard'
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

import os
from .forms import RestoreForm
import tempfile
from .models import (
    Medicine,
    Supplier,
    Sale,Purchase,
    PurchaseItem,SaleItem,StockTransaction,ActivityLog
)
from .forms import (
    MedicineForm,CustomUserCreationForm,
    SupplierForm,PurchaseForm,PurchaseItemForm,SaleForm,SaleItemForm,StockReductionForm
)
from datetime import date,timedelta
from .forms import MedicineForm
from .forms import ShopSettingsForm
from .models import ShopSettings
from django.shortcuts import (
    render,
    redirect,get_object_or_404
)
@login_required
def dashboard(request):

    medicines = Medicine.objects.count()

    suppliers = Supplier.objects.count()

    low_stock = Medicine.objects.filter(
        stock_quantity__lte=20
    ).count()

    expired = Medicine.objects.filter(
        expiry_date__lt=date.today()
    ).count()

    expiring_soon = Medicine.objects.filter(
        expiry_date__lte=date.today() + timedelta(days=30),
        expiry_date__gte=date.today()
    )

    for medicine in expiring_soon:

        medicine.days_left = (
            medicine.expiry_date -
            date.today()
        ).days

    low_stock_medicines = Medicine.objects.filter(
        stock_quantity__lte=20
    )

    expiring_count = expiring_soon.count()

    out_of_stock_count = Medicine.objects.filter(
        stock_quantity=0
    ).count()

    critical_stock_count = Medicine.objects.filter(
        stock_quantity__lte=5
    ).count()

    today_sales = Sale.objects.filter(
        sale_date=date.today()
    )

    today_sales_count = today_sales.count()

    inventory_value = sum(
        medicine.stock_quantity *
        medicine.purchase_price
        for medicine in Medicine.objects.all()
    )

    today_sales_revenue = sum(
        item.quantity * item.selling_price
        for item in SaleItem.objects.filter(
            sale__sale_date=date.today()
        )
    )

    today_purchase_cost = sum(
        item.quantity * item.purchase_price
        for item in PurchaseItem.objects.filter(
            purchase__purchase_date=date.today()
        )
    )

    today_profit = sum(
        (
            item.selling_price -
            item.medicine.purchase_price
        ) * item.quantity
        for item in SaleItem.objects.filter(
            sale__sale_date=date.today()
        )
    )

    total_sales_revenue = sum(
        item.quantity * item.selling_price
        for item in SaleItem.objects.all()
    )

    total_purchase_cost = sum(
        item.quantity * item.purchase_price
        for item in PurchaseItem.objects.all()
    )

    estimated_profit = sum(
        (
            item.selling_price -
            item.medicine.purchase_price
        ) * item.quantity
        for item in SaleItem.objects.all()
    )

    context = {

        'medicines': medicines,
        'suppliers': suppliers,
        'low_stock': low_stock,
        'expired': expired,

        'inventory_value': inventory_value,

        'low_stock_medicines': low_stock_medicines,
        'expiring_soon': expiring_soon,

        'expiring_count': expiring_count,
        'out_of_stock_count': out_of_stock_count,
        'critical_stock_count': critical_stock_count,

        'today_sales_count': today_sales_count,

        'today_sales_revenue': today_sales_revenue,
        'today_purchase_cost': today_purchase_cost,
        'today_profit': today_profit,

        'total_sales_revenue': total_sales_revenue,
        'total_purchase_cost': total_purchase_cost,
        'estimated_profit': estimated_profit,
    }

    return render(
        request,
        'inventory/dashboard.html',
        context
    )
@login_required
def medicine_list(request):

    query = request.GET.get('q')
    filter_type = request.GET.get(
    'filter'
)
    expired = request.GET.get('expired')
    expiring = request.GET.get('expiring')
    low_stock = request.GET.get('low_stock')

    medicines = Medicine.objects.all()
    stock_min = request.GET.get(
        'stock_min'
    )

    stock_max = request.GET.get(
        'stock_max'
    )

    expiry_from = request.GET.get(
        'expiry_from'
    )

    expiry_to = request.GET.get(
        'expiry_to'
    )

    if stock_min:

        medicines = medicines.filter(
            stock_quantity__gte=stock_min
        )

    if stock_max:

        medicines = medicines.filter(
            stock_quantity__lte=stock_max
        )

    if expiry_from:

        medicines = medicines.filter(
            expiry_date__gte=expiry_from
        )

    if expiry_to:

        medicines = medicines.filter(
            expiry_date__lte=expiry_to
        )
    if query:

        medicines = medicines.filter(

        Q(name__icontains=query) |

        Q(manufacturer__icontains=query) |

        Q(batch_number__icontains=query)

    )
    if filter_type == 'low_stock':

        medicines = medicines.filter(
        stock_quantity__lte=20,
        stock_quantity__gt=0
    )

    elif filter_type == 'out_of_stock':

        medicines = medicines.filter(
        stock_quantity=0
    )

    elif filter_type == 'expired':

        medicines = medicines.filter(
        expiry_date__lt=date.today()
    )

    elif filter_type == 'expiring_soon':

        medicines = medicines.filter(
        expiry_date__lte=
        date.today() + timedelta(days=30),
        expiry_date__gte=date.today()
    )
    paginator = Paginator(
        medicines,
        20
    )

    page_number = request.GET.get(
        'page'
    )

    medicines = paginator.get_page(
        page_number
    )
    return render(
        request,
        'inventory/medicine_list.html',
        {
            'medicines': medicines
        }
    )
@login_required
def supplier_list(request):


    query = request.GET.get('q')

    suppliers = Supplier.objects.all()

    supplier_name = request.GET.get(
    'supplier_name'
)

    gst_number = request.GET.get(
    'gst_number'
)

    drug_license_number = request.GET.get(
    'drug_license_number'
)

    phone = request.GET.get(
    'phone'
)

    email = request.GET.get(
    'email'
)

    if query:

        suppliers = suppliers.filter(

        Q(name__icontains=query) |

        Q(phone__icontains=query) |

        Q(email__icontains=query) |

        Q(gst_number__icontains=query) |

        Q(drug_license_number__icontains=query)

    )

    if supplier_name:

        suppliers = suppliers.filter(
        name__icontains=supplier_name
    )

    if gst_number:

        suppliers = suppliers.filter(
        gst_number__icontains=gst_number
    )

    if drug_license_number:

        suppliers = suppliers.filter(
        drug_license_number__icontains=
        drug_license_number
    )

    if phone:

        suppliers = suppliers.filter(
        phone__icontains=phone
    )

    if email:

        suppliers = suppliers.filter(
        email__icontains=email
    )

    paginator = Paginator(
    suppliers.order_by('-id'),
    20
)

    page_number = request.GET.get(
    'page'
)

    suppliers = paginator.get_page(
    page_number
)

    return render(
    request,
    'inventory/supplier_list.html',
    {
        'suppliers': suppliers
    }
)


def supplier_add(request):

    if request.method == 'POST':

        form = SupplierForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                'supplier_list'
            )

    else:

        form = SupplierForm()

    return render(
        request,
        'inventory/supplier_form.html',
        {
            'form': form
        }
    )
def supplier_edit(request, pk):

    supplier = get_object_or_404(
        Supplier,
        pk=pk
    )

    if request.method == 'POST':

        form = SupplierForm(
            request.POST,
            instance=supplier
        )

        if form.is_valid():

            form.save()

            return redirect(
                'supplier_list'
            )

    else:

        form = SupplierForm(
            instance=supplier
        )

    return render(
        request,
        'inventory/supplier_form.html',
        {
            'form': form
        }
    )
@login_required
def purchase_list(request):

    if request.user.groups.filter(
        name='Cashier'
    ).exists():

        return redirect(
            'dashboard'
        )

    purchases = Purchase.objects.all().order_by(
        '-purchase_date'
    )

    query = request.GET.get('q')

    supplier_name = request.GET.get(
        'supplier_name'
    )

    amount_min = request.GET.get(
        'amount_min'
    )

    amount_max = request.GET.get(
        'amount_max'
    )

    date_from = request.GET.get(
        'date_from'
    )

    date_to = request.GET.get(
        'date_to'
    )

    if query:

        purchases = purchases.filter(
    Q(invoice_number__icontains=query) |
    Q(supplier__name__icontains=query) |
    Q(supplier__gst_number__icontains=query) |
    Q(supplier__drug_license_number__icontains=query)
)

    if supplier_name:

        purchases = purchases.filter(
            supplier__name__icontains=supplier_name
        )

    if date_from:

        purchases = purchases.filter(
            purchase_date__gte=date_from
        )

    if date_to:

        purchases = purchases.filter(
            purchase_date__lte=date_to
        )

    filtered_purchases = []

    for purchase in purchases:

        total = purchase.total_amount

        if amount_min:

            if total < float(amount_min):
                continue

        if amount_max:

            if total > float(amount_max):
                continue

        filtered_purchases.append(
            purchase
        )

    paginator = Paginator(
        filtered_purchases,
        20
    )

    page_number = request.GET.get(
        'page'
    )

    purchases = paginator.get_page(
        page_number
    )

    return render(
        request,
        'inventory/purchase_list.html',
        {
            'purchases': purchases
        }
    )
@login_required
def sale_list(request):

    sales = Sale.objects.all().order_by(
        '-sale_date'
    )

    query = request.GET.get('q')

    customer_name = request.GET.get(
        'customer_name'
    )

    amount_min = request.GET.get(
        'amount_min'
    )

    amount_max = request.GET.get(
        'amount_max'
    )

    date_from = request.GET.get(
        'date_from'
    )

    date_to = request.GET.get(
        'date_to'
    )

    if query:

        sales = sales.filter(

            Q(invoice_number__icontains=query) |

            Q(customer_name__icontains=query) |

Q(customer_mobile__icontains=query)

        )

    if customer_name:

        sales = sales.filter(
            customer_name__icontains=customer_name
        )

    if date_from:

        sales = sales.filter(
            sale_date__gte=date_from
        )

    if date_to:

        sales = sales.filter(
            sale_date__lte=date_to
        )

    filtered_sales = []

    for sale in sales:

        total = sale.total_amount

        if amount_min:

            if total < float(amount_min):
                continue

        if amount_max:

            if total > float(amount_max):
                continue

        filtered_sales.append(
            sale
        )

    paginator = Paginator(
        filtered_sales,
        20
    )

    page_number = request.GET.get(
        'page'
    )

    sales = paginator.get_page(
        page_number
    )

    return render(
        request,
        'inventory/sale_list.html',
        {
            'sales': sales
        }
    )
def medicine_add(request):

    if request.method == 'POST':

        form = MedicineForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            form.save()

            return redirect(
                'medicine_list'
            )

    else:

        form = MedicineForm()

    return render(
        request,
        'inventory/medicine_form.html',
        {
            'form': form
        }
    )
def medicine_edit(request, pk):

    medicine = get_object_or_404(
        Medicine,
        pk=pk
    )

    if request.method == 'POST':

        form = MedicineForm(
            request.POST,
            request.FILES,
            instance=medicine
        )

        if form.is_valid():
            form.save()

            return redirect(
                'medicine_list'
            )

    else:

        form = MedicineForm(
            instance=medicine
        )

    return render(
        request,
        'inventory/medicine_form.html',
        {
            'form': form
        }
    )
def medicine_delete(request, pk):

    medicine = get_object_or_404(
        Medicine,
        pk=pk
    )

    if request.method == 'POST':

        medicine.delete()

        return redirect(
            'medicine_list'
        )

    return render(
        request,
        'inventory/confirm_delete.html',
        {
            'medicine': medicine
        }
    )
def supplier_delete(request, pk):

    supplier = get_object_or_404(
        Supplier,
        pk=pk
    )

    if request.method == 'POST':

        supplier.delete()

        return redirect(
            'supplier_list'
        )

    return render(
        request,
        'inventory/confirm_supplier_delete.html',
        {
            'supplier': supplier
        }
    )
def purchase_add(request):

    if request.method == 'POST':

        form = PurchaseForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                'purchase_list'
            )

    else:

        form = PurchaseForm()

    return render(
        request,
        'inventory/purchase_form.html',
        {
            'form': form
        }
    )
def purchase_item_add(request):

    if request.method == 'POST':

        form = PurchaseItemForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                'purchase_list'
            )

    else:

        form = PurchaseItemForm()

    return render(
        request,
        'inventory/purchase_item_form.html',
        {
            'form': form
        }
    )
@login_required
def purchase_item_list(request):
    if request.user.groups.filter(
    name='Cashier'
).exists():

        return redirect(
        'dashboard'
    )
    query = request.GET.get('q')

    items = PurchaseItem.objects.all()

    if query:

        items = items.filter(
            Q(medicine__name__icontains=query) |

        Q(purchase__invoice_number__icontains=query)
    )

    return render(
        request,
        'inventory/purchase_item_list.html',
        {
            'items': items
        }
    )
def purchase_item_delete(request, pk):

    item = get_object_or_404(
        PurchaseItem,
        pk=pk
    )

    if request.method == 'POST':

        item.medicine.stock_quantity -= item.quantity

        item.medicine.save()

        item.delete()

        return redirect(
            'purchase_item_list'
        )

    return render(
        request,
        'inventory/confirm_purchase_item_delete.html',
        {
            'item': item
        }
    )
def sale_add(request):

    if request.method == 'POST':

        form = SaleForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                'sale_list'
            )

    else:
        form = SaleForm()


    return render(
        request,
        'inventory/sale_form.html',
        {
            'form': form
        }
    )
def sale_item_add(request):

    if request.method == 'POST':

        form = SaleItemForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                'sale_list'
            )

    else:

        form = SaleItemForm()

    return render(
        request,
        'inventory/sale_item_form.html',
        {
            'form': form
        }
    )
@login_required
def sale_item_list(request):

    query = request.GET.get('q')

    items = SaleItem.objects.select_related(
        'sale',
        'medicine'
    ).all()

    if query:

        items = items.filter(

            Q(medicine__name__icontains=query) |

            Q(sale__invoice_number__icontains=query)

        )

    paginator = Paginator(
        items,
        20
    )

    page_number = request.GET.get(
        'page'
    )

    items = paginator.get_page(
        page_number
    )

    return render(
        request,
        'inventory/sale_item_list.html',
        {
            'items': items
        }
    )
def sale_item_delete(request, pk):

    item = get_object_or_404(
        SaleItem,
        pk=pk
    )

    if request.method == 'POST':

        item.medicine.stock_quantity += item.quantity

        item.medicine.save()

        item.delete()

        return redirect(
            'sale_item_list'
        )

    return render(
        request,
        'inventory/confirm_sale_item_delete.html',
        {
            'item': item
        }
    )
def sale_detail(request, pk):

    sale = get_object_or_404(
        Sale,
        pk=pk
    )

    items = SaleItem.objects.filter(
        sale=sale
    )
    

    total = sum(
        item.quantity *
        item.selling_price
        for item in items
    )
    shop = ShopSettings.objects.first()
    return render(
        request,
        'inventory/sale_detail.html',
        {
            'sale': sale,
            'items': items,
            'total': total,
        'shop': shop
        }
    )
def purchase_detail(request, pk):

    purchase = get_object_or_404(
        Purchase,
        pk=pk
    )

    items = PurchaseItem.objects.filter(
        purchase=purchase
    )

    for item in items:

        item.line_total = (
            item.quantity *
            item.purchase_price
        )

    total = sum(
        item.line_total
        for item in items
    )
    shop = ShopSettings.objects.first()
    return render(
        request,
        'inventory/purchase_detail.html',
        {
            'purchase': purchase,
            'items': items,
            'shop': shop,
            'total': total
        }
    )
def purchase_delete(request, pk):

    purchase = get_object_or_404(
        Purchase,
        pk=pk
    )

    if request.method == 'POST':

        for item in purchase.items.all():

            item.medicine.stock_quantity -= item.quantity

            item.medicine.save()

        purchase.delete()

        return redirect(
            'purchase_list'
        )

    return render(
        request,
        'inventory/confirm_purchase_delete.html',
        {
            'purchase': purchase
        }
    )
def sale_delete(request, pk):

    sale = get_object_or_404(
        Sale,
        pk=pk
    )

    if request.method == 'POST':

        for item in sale.items.all():

            item.medicine.stock_quantity += item.quantity

            item.medicine.save()

        sale.delete()

        return redirect(
            'sale_list'
        )

    return render(
        request,
        'inventory/confirm_sale_delete.html',
        {
            'sale': sale
        }
    )
def stock_transaction_list(request):

    query = request.GET.get('q')

    transactions = StockTransaction.objects.all().order_by(
        '-created_at'
    )

    if query:

        transactions = transactions.filter(
            Q(medicine__name__icontains=query) |

        Q(transaction_type__icontains=query)
        )
    transaction_type = request.GET.get(
    'type'
)

    date_from = request.GET.get(
    'date_from'
)

    date_to = request.GET.get(
    'date_to'
)

    if transaction_type:

        transactions = transactions.filter(
        transaction_type=transaction_type
    )

    if date_from:

        transactions = transactions.filter(
        created_at__date__gte=date_from
    )

    if date_to:

        transactions = transactions.filter(
        created_at__date__lte=date_to
    )
    paginator = Paginator(
    transactions,
    20
)

    page_number = request.GET.get(
    'page'
)

    transactions = paginator.get_page(
    page_number
)
    return render(
        request,
        'inventory/stock_transaction_list.html',
        {
            'transactions': transactions
        }
    )
def shop_settings(request):

    settings_obj, created = ShopSettings.objects.get_or_create(
        id=1
    )

    if request.method == 'POST':

        form = ShopSettingsForm(
            request.POST,
            instance=settings_obj
        )

        if form.is_valid():

            form.save()

            return redirect(
                'shop_settings'
            )

    else:

        form = ShopSettingsForm(
            instance=settings_obj
        )

    return render(
        request,
        'inventory/shop_settings.html',
        {
            'form': form
        }
    )
@admin_required
def backup_database(request):

    return render(
        request,
        'inventory/backup_confirm.html'
    )
@admin_required
def confirm_backup(request):

    if request.method == 'POST':

        ActivityLog.objects.create(
            user=request.user.username,
            action="Created database backup"
        )

        response = HttpResponse(
            content_type='application/json'
        )

        response[
            'Content-Disposition'
        ] = (
            'attachment; '
            'filename="backup.json"'
        )

        call_command(
            'dumpdata',
            stdout=response
        )

        return response

    return redirect(
        'backup_database'
    )
@admin_required
def restore_database(request):
    
    if request.method == 'POST':

        form = RestoreForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            uploaded_file = request.FILES[
                'backup_file'
            ]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.json'
            ) as temp_file:

                for chunk in uploaded_file.chunks():

                    temp_file.write(chunk)

                temp_path = temp_file.name

            request.session[
                'restore_file'
            ] = temp_path

            return redirect(
                'confirm_restore'
            )

    else:

        form = RestoreForm()

    return render(
        request,
        'inventory/restore_database.html',
        {
            'form': form
        }
    )
def confirm_restore(request):
    
    if request.method == 'POST':

        temp_path = request.session.get(
            'restore_file'
        )

        if temp_path:

            try:

                call_command(
                    'loaddata',
                    temp_path
                )

            except Exception as e:

                return HttpResponse(
                    str(e)
                )

            del request.session[
                'restore_file'
            ]

            messages.success(
                request,
                'Database restored successfully.'
            )
            ActivityLog.objects.create(
    user=request.user.username,
    action="Restored database"
)
            return redirect('dashboard')

    return render(
        request,
        'inventory/confirm_restore.html'
    )
@admin_required
def system_settings(request):

    return render(
        request,
        'inventory/system_settings.html'
    )
@admin_required
def user_list(request):

    if not is_admin(request.user):
        return redirect("dashboard")

    users = User.objects.select_related(
        "profile"
    ).prefetch_related(
        "groups"
    ).order_by("username")

    search = request.GET.get(
        "q"
    )

    if search:

        users = users.filter(

            Q(username__icontains=search)

            |

            Q(first_name__icontains=search)

            |

            Q(last_name__icontains=search)

            |

            Q(email__icontains=search)

            |

            Q(profile__mobile_number__icontains=search)

        )

    role = request.GET.get(
        "role"
    )

    if role:

        users = users.filter(
            groups__id=role
        )

    account = request.GET.get(
        "account"
    )

    if account == "active":

        users = users.filter(
            is_active=True
        )

    elif account == "inactive":

        users = users.filter(
            is_active=False
        )

    online = request.GET.get(
        "online"
    )

    if online == "online":

        users = users.filter(
            profile__is_online=True
        )

    elif online == "offline":

        users = users.filter(
            profile__is_online=False
        )

    paginator = Paginator(
        users,
        20
    )

    page = request.GET.get(
        "page"
    )

    users = paginator.get_page(
        page
    )

    return render(

        request,

        "inventory/user_list.html",

        {

            "users": users,

            "roles": Group.objects.all(),

            "search": search,

            "selected_role": role,

            "selected_account": account,

            "selected_online": online,

        }

    )
@login_required
@admin_required
def toggle_user_status(request, pk):

    user = get_object_or_404(
        User,
        pk=pk
    )

    if user == request.user:

        messages.error(

            request,

            "You cannot deactivate your own account."

        )

        return redirect(
            "user_list"
        )

    admin_group = Group.objects.get(
        name="Admin"
    )

    active_admins = User.objects.filter(

        groups=admin_group,

        is_active=True

    ).count()

    if (

        user.groups.filter(
            name="Admin"
        ).exists()

        and

        user.is_active

        and

        active_admins == 1

    ):

        messages.error(

            request,

            "Cannot deactivate the last active administrator."

        )

        return redirect(
            "user_list"
        )

    user.is_active = not user.is_active

    user.save()

    ActivityLog.objects.create(

        user=request.user.username,

        action=f"{'Activated' if user.is_active else 'Deactivated'} account {user.username}"

    )

    messages.success(

        request,

        f"{user.username} account updated."

    )

    return redirect(
        "user_list"
    )
@admin_required
@login_required
def user_add(request):

    if request.method == "POST":

        form = CustomUserCreationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.first_name = form.cleaned_data["first_name"]

            user.last_name = form.cleaned_data["last_name"]

            user.email = form.cleaned_data["email"].strip().lower()

            user.is_active = True

            user.save()

            UserProfile.objects.create(

                user=user,

                mobile_number=form.cleaned_data["mobile_number"],

                address=form.cleaned_data["address"],

                is_online=False

            )

            role = form.cleaned_data["role"]

            user.groups.add(role)

            ActivityLog.objects.create(

                user=request.user.username,

                action=f"Created user '{user.username}'"

            )

            messages.success(

                request,

                "User created successfully."

            )

            return redirect("user_list")

    else:

        form = CustomUserCreationForm()

    return render(

        request,

        "inventory/user_form.html",

        {

            "form": form

        }

    )
@admin_required
def user_delete(request, pk):
    if not is_admin(request.user):

        return redirect(
        'dashboard'
    )
    user = get_object_or_404(
        User,
        pk=pk
    )
    if request.user == user:

        return redirect(
            'user_list'
        )
    if user.is_superuser:

        return redirect(
        'user_list'
    )
    if request.user == user:

        return redirect(
            'user_list'
        )

    if request.method == 'POST':

        ActivityLog.objects.create(
            user=request.user.username,
            action=f"Deleted user {user.username}"
    )

        user.delete()

        return redirect(
        'user_list'
    )

    return render(
        request,
        'inventory/user_confirm_delete.html',
        {
            'user_obj': user
        }
    )
@admin_required
def toggle_user_status(request, pk):

    if not is_admin(request.user):

        return redirect(
            'dashboard'
        )

    user = get_object_or_404(
        User,
        pk=pk
    )

    if user == request.user:

        messages.error(
            request,
            "You cannot deactivate your own account."
        )

        return redirect(
            'user_list'
        )

    if user.is_superuser:

        messages.error(
            request,
            "Superuser status cannot be changed."
        )

        return redirect(
            'user_list'
        )

    user.is_active = not user.is_active

    user.save()

    status = (
        "Activated"
        if user.is_active
        else
        "Deactivated"
    )

    ActivityLog.objects.create(

        user=request.user.username,

        action=f"{status} user {user.username}"

    )

    messages.success(

        request,

        f"{user.username} has been {status.lower()}."

    )

    return redirect(
        'user_list'
    )
@admin_required
def user_edit(request, pk):

    if not is_admin(request.user):

        return redirect(
            'dashboard'
        )

    user = get_object_or_404(
        User,
        pk=pk
    )
    editing_self = (
    request.user == user
)
    profile, created = UserProfile.objects.get_or_create(
        user=user
    )

    if request.method == "POST":

        form = UserEditForm(

            request.POST,

            instance=user

        )

        if form.is_valid():

            user = form.save()

            profile.mobile_number = form.cleaned_data[
                "mobile_number"
            ]

            profile.address = form.cleaned_data[
                "address"
            ]

            profile.save()

            user.groups.clear()

            if not editing_self:

                user.groups.clear()

                user.groups.add(

                    form.cleaned_data[
            "role"
        ]

    )

            ActivityLog.objects.create(

                user=request.user.username,

                action=f"Updated user {user.username}"

            )

            messages.success(

                request,

                "User updated successfully."

            )

            return redirect(
                "user_list"
            )

    else:

        form = UserEditForm(

            instance=user,

            initial={

                "mobile_number": profile.mobile_number,

                "address": profile.address,

                "role": user.groups.first(),

                "is_active": user.is_active

            }

        )
        if editing_self:

            form.fields["role"].disabled = True

    return render(

        request,

        "inventory/user_edit.html",

        {

            "form": form,

            "user_obj": user

        }

    )
def is_admin(user):

    return user.groups.filter(
        name='Admin'
    ).exists()
def user_change_password(request, pk):

    if not is_admin(request.user):

        if request.user.id != pk:

            return redirect(
            'dashboard'
        )

    user = get_object_or_404(
        User,
        pk=pk
    )

    if request.method == 'POST':

        form = SetPasswordForm(
            user,
            request.POST
        )

        if form.is_valid():

            new_password = form.cleaned_data[
                'new_password1'
            ]

            if user.check_password(
                new_password
            ):

                form.add_error(
                'new_password1',
                'New password cannot be the same as the current password.'
                )

                return render(
                    request,
                    'inventory/user_change_password.html',
                    {
                        'form': form,
                        'user_obj': user
                    }
                )

            form.save()

            update_session_auth_hash(
                request,
                user
            )

            ActivityLog.objects.create(
                user=request.user.username,
                action=f"Changed password for {user.username}"
            )

            messages.success(
                request,
                f'Password updated for {user.username}'
            )

            return redirect(
                'user_list'
            )

    else:

        form = SetPasswordForm(user)

    return render(
        request,
        'inventory/user_change_password.html',
        {
            'form': form,
            'user_obj': user
        }
    )
def activity_logs(request):

    if not is_admin(request.user):
        return redirect('dashboard')

    logs = ActivityLog.objects.all()
    paginator = Paginator(
    logs,
    20
)

    page_number = request.GET.get(
    'page'
)

    logs = paginator.get_page(
    page_number
)
    return render(
        request,
        'inventory/activity_logs.html',
        {
            'logs': logs
        }
    )
@login_required
def profile(request):

    return render(
        request,
        'inventory/profile.html',
        {
            'user_obj': request.user
        }
    )
def system_information(request):

    if not is_admin(request.user):

        return redirect(
            'dashboard'
        )

    context = {

        'total_medicines':
        Medicine.objects.count(),

        'total_suppliers':
        Supplier.objects.count(),

        'total_purchases':
        Purchase.objects.count(),

        'total_sales':
        Sale.objects.count(),

        'total_users':
        User.objects.count(),

        'total_transactions':
        StockTransaction.objects.count(),

    }

    return render(
        request,
        'inventory/system_information.html',
        context
    )
def get_role(user):

    group = user.groups.first()

    if group:

        return group.name

    return None
@login_required
def adjust_stock(
    request,
    medicine_id
):

    medicine = get_object_or_404(
        Medicine,
        id=medicine_id
    )

    if request.method == 'POST':

        form = StockReductionForm(
            request.POST
        )

        if form.is_valid():

            reduction = form.save(
                commit=False
            )

            if (
                reduction.quantity >
                medicine.stock_quantity
            ):

                messages.error(
                    request,
                    'Cannot reduce more than available stock.'
                )

                return render(
                    request,
                    'inventory/adjust_stock.html',
                    {
                        'form': form,
                        'medicine': medicine,
                    }
                )

            reduction.medicine = medicine

            reduction.previous_stock = (
                medicine.stock_quantity
            )

            medicine.stock_quantity -= (
                reduction.quantity
            )

            reduction.new_stock = (
                medicine.stock_quantity
            )

            reduction.adjusted_by = (
                request.user
            )

            medicine.save()

            reduction.save()

            messages.success(
                request,
                'Stock adjusted successfully.'
            )
            StockTransaction.objects.create(
    medicine=medicine,
    transaction_type=reduction.reason,
    quantity=reduction.quantity,
    notes='Stock adjusted'
)
            return redirect(
                'medicine_list'
            )

    else:

        form = StockReductionForm()

    return render(
        request,
        'inventory/adjust_stock.html',
        {
            'form': form,
            'medicine': medicine,
        }
    )
@login_required
def undo_stock_transaction(request, id):

    transaction = get_object_or_404(
        StockTransaction,
        id=id
    )

    if transaction.transaction_type not in [
        'EXPIRED',
        'DAMAGED',
        'LOST'
    ]:

        messages.error(
            request,
            'This transaction cannot be undone.'
        )

        return redirect(
            'stock_transaction_list'
        )

    transaction.medicine.stock_quantity += (
        transaction.quantity
    )

    transaction.medicine.save()

    transaction.delete()

    messages.success(
        request,
        'Stock adjustment undone successfully.'
    )

    return redirect(
        'stock_transaction_list'
    )
def forgot_username(request):

    print("VIEW START")

    form = ForgotUsernameForm()

    if request.method == "POST":

        print("POST RECEIVED")

        form = ForgotUsernameForm(request.POST)

        if form.is_valid():

            print("FORM VALID")

            email = form.cleaned_data["email"].strip().lower()

            print("EMAIL:", email)

            user = User.objects.filter(
                email__iexact=email
            ).first()

            print("USER:", user)

            if user:

                print("SENDING EMAIL")

                success, msg = send_email(
                    recipient=email,
                    subject="Medical Shop ERP - Username Recovery",
                    message=f"Your username is: {user.username}"
                )

                print(success, msg)

            messages.success(
                request,
                "If an account exists with this email, your username has been sent."
            )

            return redirect("login")

        else:

            print(form.errors)

    return render(
        request,
        "registration/forgot_username.html",
        {
            "form": form
        }
    )

def verify_otp(request):

    email = request.session.get("reset_email")

    if not email:

        messages.error(

            request,

            "Password reset session expired."

        )

        return redirect("forgot_password")

    user = User.objects.filter(

        email__iexact=email

    ).first()

    if not user:

        messages.error(

            request,

            "Invalid request."

        )

        return redirect("forgot_password")

    form = OTPVerificationForm()

    if request.method == "POST":

        form = OTPVerificationForm(request.POST)

        if form.is_valid():

            otp = form.cleaned_data["otp"]

            otp_record = PasswordResetOTP.objects.filter(

                user=user,

                otp=otp

            ).first()

            if not otp_record:

                latest = PasswordResetOTP.objects.filter(

                user=user

                ).first()

                if latest:

                    latest.attempts += 1

                    latest.save()

                    if latest.attempts >= 5:

                        latest.delete()

                        messages.error(

                        request,

                        "Maximum OTP attempts exceeded."

                        )

                        return redirect(

                "forgot_password"

            )

                messages.error(

        request,

        "Invalid OTP."

    )

                return render(

        request,

        "registration/verify_otp.html",

        {

            "form": form

        }

    )

            if otp_record.is_expired():

                otp_record.delete()

                messages.error(

                    request,

                    "OTP has expired."

                )

                return redirect(

                    "forgot_password"

                )
            otp_record.attempts = 0

            otp_record.save()
            request.session["otp_verified"] = True

            return redirect(

                "reset_password"

            )

    return render(

        request,

        "registration/verify_otp.html",

        {

            "form": form

        }

    )

def forgot_password(request):

    form = ForgotPasswordForm()

    if request.method == "POST":

        form = ForgotPasswordForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"].strip().lower()

            user = User.objects.filter(
                email__iexact=email
            ).first()

            if user:

                PasswordResetOTP.objects.filter(
                    user=user
                ).delete()

                otp = str(
                    random.randint(
                        100000,
                        999999
                    )
                )

                PasswordResetOTP.objects.create(

                    user=user,

                    otp=otp

                )

                send_email(

                    recipient=email,

                    subject="Medical Shop ERP - Password Reset OTP",

                    message=f"""
Hello {user.first_name or user.username},

Your OTP is

{otp}

This OTP is valid for 5 minutes.

If you did not request this password reset,
please ignore this email.

Regards,
Medical Shop ERP
"""

                )

            messages.success(

                request,

                "If an account exists with this email, an OTP has been sent."

            )

            request.session["reset_email"] = email

            return redirect("verify_otp")

    return render(

        request,

        "registration/forgot_password.html",

        {

            "form": form

        }

    )
@login_required
@admin_required
def email_settings(request):

    email_config = EmailSettings.objects.first()

    if request.method == "POST":

        form = EmailSettingsForm(

            request.POST,

            instance=email_config

        )

        if form.is_valid():

            form.save()

            ActivityLog.objects.create(

                user=request.user.username,

                action="Updated Email Configuration"

            )

            messages.success(

                request,

                "Email configuration saved."

            )

            return redirect(

                "email_settings"

            )

    else:

        form = EmailSettingsForm(

            instance=email_config

        )

    return render(

        request,

        "inventory/email_settings.html",

        {

            "form": form

        }

    )
@login_required
@admin_required
def test_email(request):

    config = EmailSettings.objects.filter(
        is_active=True
    ).first()

    if not config:

        messages.error(

            request,

            "No active email configuration found."

        )

        return redirect(

            "email_settings"

        )

    success, message = send_email(

        recipient=config.sender_email,

        subject="Medical Shop ERP - Test Email",

        message="""
Congratulations!

Your Email Configuration is working successfully.

This email was sent from your Medical Shop ERP.

You can now use:

• Forgot Password
• Forgot Username
• OTP Verification
• Future Notifications

Regards,
Medical Shop ERP
"""

    )

    if success:

        messages.success(

            request,

            message

        )

    else:

        messages.error(

            request,

            message

        )

    return redirect(

        "email_settings"

    )
def resend_otp(request):

    email = request.session.get("reset_email")

    if not email:

        messages.error(

            request,

            "Session expired."

        )

        return redirect("forgot_password")

    user = User.objects.filter(

        email__iexact=email

    ).first()

    if not user:

        return redirect("forgot_password")

    old = PasswordResetOTP.objects.filter(

        user=user

    ).first()

    if old:

        seconds = (
        timezone.now() - old.created_at
    ).total_seconds()

        if seconds < 60:

            remaining = 60 - int(seconds)

            messages.error(

            request,

            f"Please wait {remaining} seconds before requesting another OTP."

        )

            return redirect(
            "verify_otp"
        )

        if old.resend_count >= 5:

            messages.error(

            request,

            "Maximum OTP resend limit reached."

        )

            return redirect(
            "forgot_password"
        )

        resend_count = old.resend_count + 1

        old.delete()

    else:

        resend_count = 0

    otp = str(

        random.randint(

            100000,

            999999

        )

    )

    PasswordResetOTP.objects.create(

        user=user,

        otp=otp,

        resend_count=resend_count,

        expires_at=timezone.now() + timedelta(minutes=5)

    )

    send_email(

        recipient=user.email,

        subject="Password Reset OTP",

        message=f"""
Your new OTP is:

{otp}

Valid for 5 minutes.
"""

    )

    ActivityLog.objects.create(

        user=user.username,

        action="Resent Password Reset OTP"

    )

    messages.success(

        request,

        "A new OTP has been sent."

    )

    return redirect(

        "verify_otp"

    )
def setup(request):

    status = InstallationStatus.objects.first()

    if status and status.is_completed:

        return redirect("login")

    if request.method == "POST":

        form = SetupForm(request.POST)

        if form.is_valid():

            request.session["setup_data"] = {

                "shop_name": form.cleaned_data["shop_name"],

                "owner_first_name": form.cleaned_data["owner_first_name"],

                "owner_last_name": form.cleaned_data["owner_last_name"],
                "email": form.cleaned_data["email"],

                "mobile": form.cleaned_data["mobile"],

                "username": form.cleaned_data["username"],

                "password": form.cleaned_data["password"]

            }

            try:

                InstallationService.send_setup_otp(

                    form.cleaned_data["email"]

                )

                messages.success(

                    request,

                    "OTP has been sent to your email."

                )

                return redirect("setup_verify")

            except Exception as e:

                messages.error(

                    request,

                    str(e)

                )

    else:

        form = SetupForm()

    return render(

        request,

        "inventory/setup.html",

        {

            "form": form

        }

    )
def setup_verify(request):

    if "setup_data" not in request.session:

        messages.error(
            request,
            "Setup session expired."
        )

        return redirect("setup")

    if request.method == "POST":

        otp = request.POST.get("otp")

        data = request.session["setup_data"]

        try:

            record = SetupOTP.objects.get(
                email=data["email"]
            )

        except SetupOTP.DoesNotExist:

            messages.error(
                request,
                "OTP not found."
            )

            return redirect("setup")

        if record.expired():

            messages.error(
                request,
                "OTP has expired."
            )

            return redirect("setup_verify")

        if record.otp != otp:

            messages.error(
                request,
                "Invalid OTP."
            )

            return redirect("setup_verify")

        # Continue here after OTP is verified

        return redirect("setup_install")

    form = SetupOTPForm()

    return render(

        request,

        "inventory/setup_verify_otp.html",

        {

            "form": form

        }

    )
def home(request):

    status = InstallationStatus.objects.first()

    if not status:

        return redirect("setup")

    if not status.is_completed:

        return redirect("setup")

    return redirect("login")
from .services import InstallationService
from django.contrib import messages
from django.shortcuts import redirect

def setup_resend_otp(request):

    data = request.session.get("setup_data")

    if not data:

        messages.error(
            request,
            "Setup session expired."
        )

        return redirect("setup")

    try:

        InstallationService.send_setup_otp(
            data["email"]
        )

        messages.success(
            request,
            "A new OTP has been sent."
        )

    except Exception as e:

        messages.error(
            request,
            str(e)
        )

    return redirect("setup_verify")