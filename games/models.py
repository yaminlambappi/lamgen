from django.db import models

class SignalingRoom(models.Model):
    code = models.CharField(max_length=4, unique=True)
    offer = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    host_ice = models.TextField(null=True, blank=True) # JSON array of candidates
    guest_ice = models.TextField(null=True, blank=True) # JSON array of candidates
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
