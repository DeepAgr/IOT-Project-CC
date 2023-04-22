from django.db import models

# Create your models here.

class SensorData(models.Model):
    temperature = models.FloatField(null=True)
    humidity = models.FloatField(null=True)
    gas_value = models.FloatField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Temperature: {self.temperature}, Humidity: {self.humidity}, Gas Value: {self.gas_value}, Timestamp: {self.timestamp}'
