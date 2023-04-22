# utils.py

from django.conf import settings
from django.core.mail import send_mail
from home.models import SensorData


def send_alert_email():
    # Get the latest sensor data
    latest_data = SensorData.objects.order_by('-timestamp').first()
    # print("here1 hjgkghlcghjhkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkghghghgkkkkkkkkkk")

    # Check if any sensor value is above the critical threshold
    if (latest_data.temperature > settings.CRITICAL_TEMP or
            latest_data.humidity > settings.CRITICAL_HUMIDITY or
            latest_data.gas_value > settings.CRITICAL_GAS_VALUE):

        # Construct the email message
        subject = 'Sensor data alert!'
        # print(subject)
        message = f"Alert: Sensor data is above critical threshold!\n\nTemperature: {latest_data.temperature}\nHumidity: {latest_data.humidity}\nGas value: {latest_data.gas_value}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['agrawal.14@iitj.ac.in', 'anuman23840@gmail.com']

        # Send the email
        send_mail(subject, message, from_email, recipient_list)
