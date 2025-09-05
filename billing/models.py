import uuid
from django.db import models
from django.utils import timezone

def gen_product_id():
    return uuid.uuid4().hex[:8].upper()

class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True, db_index=True, default=gen_product_id)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    available_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.product_id})"

class Purchase(models.Model):
    customer_email = models.EmailField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Invoice #{self.id} - {self.customer_email}"

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Denomination(models.Model):
    value = models.PositiveIntegerField(unique=True)  # e.g., 2000, 500, 100...
    count_available = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-value']

    def __str__(self):
        return f"₹{self.value} x {self.count_available}"

class ChangeDenomination(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='change_denominations')
    denomination_value = models.PositiveIntegerField(blank=True,null=True)
    count_given = models.PositiveIntegerField()

    def __str__(self):
        return f"#{self.purchase_id}: ₹{self.denomination_value} x {self.count_given}"
