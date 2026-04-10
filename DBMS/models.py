from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# --- Audit & Activity ---
class AuditLog(models.Model):
    ACTIONS = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('READ', 'Read'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} {self.object_id}"


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} {self.action} {self.model_name} ({self.object_id}) at {self.timestamp}"


# --- Core Models ---
class Rank(models.Model):
    rank_name = models.CharField(max_length=100)

    def __str__(self):
        return self.rank_name


class Case(models.Model):
    bereaved_member_name = models.CharField(max_length=100)
    relation = models.CharField(max_length=50)
    date_reported = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bereaved_member_name} ({self.relation})"

    def total_contributions(self):
        return sum(c.contribution for c in self.contribution_set.all())

    def total_expenditures(self):
        return sum(e.amount for e in self.expenditure_set.all())

    def balance(self):
        return self.total_contributions() - self.total_expenditures()


class Contribution(models.Model):
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)
    names = models.CharField(max_length=100)
    contribution = models.DecimalField(max_digits=10, decimal_places=2)
    contact = models.CharField(max_length=20)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    date_of_contribution = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.names} - {self.contribution}"


# --- New Model for Expenditure ---
class Expenditure(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    handled_by = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Prevent overspending
        if self.case.balance() < self.amount:
            raise ValueError("Expenditure exceeds available balance for this case.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.amount}"
