from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Purchase

@shared_task
def send_invoice_email(purchase_id):
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        return False

    subject = f"Invoice #{purchase.id}"
    body = render_to_string("billing/invoice_email.html", {"purchase": purchase})
    email = EmailMessage(subject=subject, body=body, to=[purchase.customer_email])
    email.content_subtype = "html"
    email.send(fail_silently=False)
    return True
