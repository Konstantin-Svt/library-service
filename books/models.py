from django.db import models


class Book(models.Model):
    class CoverType(models.TextChoices):
        SOFT = "SOFT", "Soft"
        HARD = "HARD", "Hard"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=32, choices=CoverType.choices, default=CoverType.SOFT
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField()

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
