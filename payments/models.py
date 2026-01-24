from django.db import models


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class PaymentType(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(choices=PaymentStatus.choices, max_length=64)
    type = models.CharField(choices=PaymentType.choices, max_length=64)
    borrowing = models.ForeignKey(
        "borrowings.Borrowing",
        on_delete=models.SET_NULL,
        null=True,
        related_name="payments",
    )
    session_url = models.URLField()
    session_id = models.CharField(max_length=200)
    money_to_pay = models.DecimalField(decimal_places=2, max_digits=20)

    def __str__(self):
        return (
            f"session_url: {self.session_url}, "
            f"session_id: {self.session_id}, "
            f"status: {self.status}"
        )
