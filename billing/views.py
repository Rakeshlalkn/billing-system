# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import Product, Purchase, PurchaseItem, Denomination, ChangeDenomination
from .tasks import send_invoice_email

ROUND = lambda d: d.quantize(Decimal('0.01'), rounding='ROUND_HALF_UP')

@login_required
def dashboard(request):
    return render(request, "billing/dashboard.html")

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "billing/product_list.html", {"products": products})

@login_required
def product_add(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id", "").strip() or None
        name = request.POST.get("name", "").strip()
        price_raw = request.POST.get("price", "0").strip()
        tax_raw = request.POST.get("tax", "0").strip()
        stock_raw = request.POST.get("stock", "0").strip()

        if not name:
            messages.error(request, "Product name is required.")
            return redirect("product_add")

        try:
            price = ROUND(Decimal(price_raw))
        except Exception:
            price = ROUND(Decimal("0"))
        try:
            tax = ROUND(Decimal(tax_raw))
        except Exception:
            tax = ROUND(Decimal("0"))
        try:
            stock = max(0, int(stock_raw))
        except Exception:
            stock = 0

        if product_id:
            Product.objects.update_or_create(
                product_id=product_id,
                defaults={
                    "name": name,
                    "price": price,
                    "tax_percentage": tax,
                    "available_stock": stock,
                }
            )
        else:
            Product.objects.create(
                name=name,
                price=price,
                tax_percentage=tax,
                available_stock=stock
            )

        messages.success(request, "Product saved.")
        return redirect("product_list")

    return render(request, "billing/product_form.html")

@login_required
def denomination_list(request):
    denoms = Denomination.objects.all().order_by('-value')
    return render(request, "billing/denomination_list.html", {"denoms": denoms})

@login_required
def denomination_add(request):
    if request.method == "POST":
        value_raw = request.POST.get("value", "0").strip()
        count_raw = request.POST.get("count", "0").strip()

        try:
            value = int(value_raw)
            if value <= 0:
                raise ValueError
        except:
            messages.error(request, "Invalid denomination value.")
            return redirect("denomination_add")

        try:
            count = max(0, int(count_raw))
        except:
            count = 0

        Denomination.objects.update_or_create(
            value=value,
            defaults={"count_available": count}
        )

        messages.success(request, "Denomination saved.")
        return redirect("denomination_list")

    return render(request, "billing/denomination_form.html")

@login_required
def billing_page(request):
    products = Product.objects.all()
    denominations = Denomination.objects.all().order_by('-value')

    if request.method == "POST":
        customer_email = (request.POST.get("customer_email") or "").strip()
        product_ids = request.POST.getlist("product_id[]")
        quantities = request.POST.getlist("quantity[]")
        paid_raw = request.POST.get("paid_amount", "0").strip()

        # Update denominations if provided
        for denom in denominations:
            field = f"denom_{denom.value}"
            v = request.POST.get(field)
            if v is not None:
                try:
                    new_count = int(v)
                    denom.count_available = max(0, new_count)
                    denom.save(update_fields=['count_available'])
                except Exception:
                    pass

        if not customer_email:
            messages.error(request, "Customer email is required.")
            return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})

        try:
            paid = ROUND(Decimal(paid_raw))
        except:
            paid = Decimal('0.00')

        items = []
        for pid, qty in zip(product_ids, quantities):
            pid = (pid or "").strip()
            if not pid:
                continue
            try:
                qty_i = int(qty)
            except Exception:
                qty_i = 0
            if qty_i <= 0:
                continue
            try:
                product = Product.objects.get(product_id=pid)
            except Product.DoesNotExist:
                messages.error(request, f"Product not found (ID={pid}).")
                return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})
            if product.available_stock < qty_i:
                messages.error(request, f"Not enough stock for {product.name}. Available: {product.available_stock}")
                return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})
            items.append((product, qty_i))

        if not items:
            messages.error(request, "Please select at least one product.")
            return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})

        try:
            with transaction.atomic():
                subtotal = Decimal('0.00')
                tax_total = Decimal('0.00')
                total = Decimal('0.00')

                purchase = Purchase.objects.create(customer_email=customer_email)

                for product, qty in items:
                    line_sub = product.price * Decimal(qty)
                    line_tax = line_sub * (product.tax_percentage / Decimal('100'))
                    line_total = ROUND(line_sub + line_tax)
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        product=product,
                        quantity=qty,
                        unit_price=product.price,
                        tax_percentage=product.tax_percentage,
                        line_total=line_total
                    )
                    product.available_stock -= qty
                    product.save(update_fields=['available_stock'])

                    subtotal += line_sub
                    tax_total += line_tax
                    total += line_total

                subtotal = ROUND(subtotal)
                tax_total = ROUND(tax_total)
                total = ROUND(total)

                if paid < total:
                    raise ValueError("Paid amount is less than total.")

                purchase.subtotal = subtotal
                purchase.tax_total = tax_total
                purchase.total = total
                purchase.paid_amount = paid
                purchase.balance = ROUND(paid - total)
                purchase.save()

                change_to_give = int(purchase.balance.quantize(Decimal('0'), rounding='ROUND_HALF_UP'))

                ChangeDenomination.objects.filter(purchase=purchase).delete()

                if change_to_give > 0:
                    for denom in Denomination.objects.all().order_by('-value'):
                        if change_to_give <= 0:
                            break
                        denom_value = denom.value
                        needed = change_to_give // denom_value
                        give = min(needed, denom.count_available)
                        if give > 0:
                            ChangeDenomination.objects.create(
                                purchase=purchase,
                                denomination_value=denom_value,
                                count_given=give
                            )
                            denom.count_available -= give
                            denom.save(update_fields=['count_available'])
                            change_to_give -= give * denom_value

                    if change_to_give > 0:
                        raise ValueError("Not enough denominations to give full change.")

                send_invoice_email.delay(purchase.id)

        except Exception as e:
            messages.error(request, f"Failed to create purchase: {str(e)}")
            return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})

        return redirect("invoice_page", purchase_id=purchase.id)

    return render(request, "billing/billing_page.html", {"products": products, "denominations": denominations})

@login_required
def invoice_page(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    return render(request, "billing/invoice.html", {"purchase": purchase})

@login_required
def bill_history(request):
    purchases = Purchase.objects.order_by('-created_at')
    return render(request, "billing/bill_history.html", {"purchases": purchases})

@login_required
def customer_history(request):
    email = None
    purchases = []
    if request.method == "POST":
        email = request.POST.get("customer_email", "").strip()
        if email:
            purchases = Purchase.objects.filter(customer_email__iexact=email).order_by('-created_at')
    return render(request, "billing/customer_history.html", {"email": email, "purchases": purchases})