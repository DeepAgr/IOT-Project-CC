from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.conf import settings
import pandas as pd
from home.models import SensorData

# def send_sensor_data_email():
#     # Get the date range for the previous month
#     today = datetime.today()
#     first_day_of_previous_month = datetime(today.year, today.month-1, 1)
#     last_day_of_previous_month = first_day_of_previous_month.replace(day=28) + timedelta(days=4)
#     last_day_of_previous_month = last_day_of_previous_month - timedelta(days=last_day_of_previous_month.day)
    
#     # Get the sensor data for the previous month
#     sensor_data = SensorData.objects.filter(timestamp__range=(first_day_of_previous_month, last_day_of_previous_month))
    
#     # Create a Pandas dataframe from the sensor data
#     df = pd.DataFrame(list(sensor_data.values()))

#     # Create an Excel file from the dataframe
#     filename = 'sensor_data_' + last_day_of_previous_month.strftime('%Y-%m') + '.xlsx'
#     df.to_excel(filename, index=False)
    
#     # Send the email with the Excel file as an attachment
#     subject = 'Sensor data for ' + last_day_of_previous_month.strftime('%B %Y')
#     message = 'Please find attached the sensor data for ' + last_day_of_previous_month.strftime('%B %Y') + '.'

#     from_email = settings.EMAIL_HOST_USER
#     recipient_list = ['agrawal.14@iitj.ac.in', 'anuman23840@gmail.com']
#     email = EmailMessage(subject, message, from_email, recipient_list)
#     email.attach_file(filename)
#     email.send()

#     # Delete the sensor data for the previous month
#     # sensor_data.delete()



# myapp/tasks.py

from datetime import date, timedelta
import pandas as pd
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from home.models import SensorData
from django.conf import settings

def send_sensor_data_email():
    # Get the date of yesterday
    yesterday = date.today() - timedelta(days=1)

    # Get all sensor data records for yesterday
    sensor_data = SensorData.objects.filter(date__date=yesterday)

    # Create a Pandas dataframe from the sensor data
    data_dict = {'timestamp': [], 'temperature': [], 'humidity': []}
    for record in sensor_data:
        data_dict['timestamp'].append(record.timestamp)
        data_dict['temperature'].append(record.temperature)
        data_dict['humidity'].append(record.humidity)
    data_df = pd.DataFrame(data_dict)

    # Generate an Excel file from the data
    excel_file = pd.ExcelWriter('sensor_data.xlsx')
    data_df.to_excel(excel_file, index=False)
    excel_file.save()

    # Send the email with the Excel file attached
    email_subject = 'Sensor Data for {}'.format(yesterday.strftime('%m/%d/%Y'))
    email_body = 'Please find attached the sensor data for'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = ['agrawal.14@iitj.ac.in', 'anuman23840@gmail.com']
    email = EmailMessage(
        email_subject,
        email_body,
        from_email,
        recipient_list
    )
    email.attach_file('sensor_data.xlsx')
    email.send()

    # Delete the sensor data records for yesterday
    # sensor_data.delete()
