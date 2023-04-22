# from datetime import datetime, timedelta
# from django.core.mail import EmailMessage
from django.conf import settings
# import pandas as pd
# from home.models import SensorData

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

    # from_email = settings.EMAIL_HOST_USER
    # recipient_list = ['agrawal.14@iitj.ac.in', 'anuman23840@gmail.com']
#     email = EmailMessage(subject, message, from_email, recipient_list)
#     email.attach_file(filename)
#     email.send()

#     # Delete the sensor data for the previous month
#     # sensor_data.delete()







from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from home.models import SensorData
from datetime import datetime, timedelta
import pandas as pd

def send_sensor_data_email():
    # Get today's date and the date for the previous day
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    
    # Get the sensor data for the previous day
    sensor_data = SensorData.objects.filter(timestamp__date=yesterday)
    
    if sensor_data.exists():
        # Create a pandas dataframe of the sensor data
        data = []
        for reading in sensor_data:
            data.append({
                'Temperature': reading.temperature,
                'Humidity': reading.humidity,
                'Gas Value': reading.gas_value,
                'Timestamp': reading.timestamp
            })
        df = pd.DataFrame(data)
        
        # Convert the dataframe to an Excel file
        excel_file = pd.ExcelWriter('sensor_data.xlsx')
        df.to_excel(excel_file, index=False)
        excel_file.save()
        
        # Send the email with the Excel file as an attachment
        subject = 'Sensor Data for {}'.format(yesterday.strftime('%m/%d/%Y'))
        body = render_to_string('sensor_data_email.html', {'date': yesterday})
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['agrawal.14@iitj.ac.in', 'anuman23840@gmail.com']
        email = EmailMessage(subject, body, from_email, recipient_list)
        email.attach_file('sensor_data.xlsx')
        email.send()
        
        # Delete the sensor data for the previous day from the database
        sensor_data.delete()

