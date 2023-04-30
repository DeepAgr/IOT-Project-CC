from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest
from home.models import SensorData
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings

# from django.db.models import Avg
from django.db.models import Min, Max, Avg
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.conf import settings
from django.views.decorators.http import require_GET
from django.utils import timezone

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
import os
from matplotlib.figure import Figure


def sensor_data_api2(request):
    sensor_data = list(SensorData.objects.values("timestamp", "temperature"))
    return JsonResponse(sensor_data, safe=False)


def line_chart_view(request):
    import datetime

    start_date = request.POST.get("startDate")
    end_date = request.POST.get("endDate")
    print(start_date)
    print(end_date)
    # Convert start and end dates to datetime objects
    # import datetime

    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.datetime.strptime(
        end_date, "%Y-%m-%d"
    ) + datetime.timedelta(days=1)

    # sd = datetime.strptime(start_date, "%Y-%m-%d")
    # ed = datetime.strptime(end_date, "%Y-%m-%d")
    # print(sd)
    # print(end_date)
    if end_datetime <= start_datetime:
        messages.error(request, "End date must be ahead of start date.")
        return redirect("export_data")
    else:
        # Get data from database between start and end dates
        data = SensorData.objects.filter(
            timestamp__range=[start_datetime, end_datetime]
        )

        # Create a list to hold the rows of the CSV file
        rows = [["Timestamp", "Temperature", "Humidity", "Gas Value"]]

        # Add data to the rows list
        for d in data:
            rows.append(
                [
                    d.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    d.temperature,
                    d.humidity,
                    d.gas_value,
                ]
            )

        # print(type(rows))

        data_dict = {
            "timestamps": [],
            "temperatures": [],
            "humidities": [],
            "gas_values": [],
        }
        latest_data = SensorData.objects.filter(
            timestamp__range=[start_datetime, end_datetime]
        )
        for edata in latest_data:
            data_dict["timestamps"].append(
                edata.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            data_dict["temperatures"].append(edata.temperature)
            data_dict["humidities"].append(edata.humidity)
            data_dict["gas_values"].append(edata.gas_value)
        # print(data_dict)
    # Retrieve data from Django database
    # data = SensorData.objects.all()
    data = SensorData.objects.filter(timestamp__range=[start_datetime, end_datetime])

    # Create a new figure object
    fig = Figure(figsize=(6, 4), dpi=100)

    # Add a subplot to the figure
    ax = fig.add_subplot(1, 1, 1)

    # Create a line plot of the data
    ax.plot([item.timestamp for item in data], [item.humidity for item in data])

    # Set the chart title and axis labels
    ax.set_title("My Line Chart")
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")

    # Save the figure to a PNG file in the "static" directory of the Django project
    fig.savefig(os.path.join(os.getcwd(), "static", "image.png"))

    # Create a PIL Image object from the saved file
    image = Image.open(os.path.join(os.getcwd(), "static", "image.png"))

    # Create a new buffer to hold the PDF data
    buffer = io.BytesIO()

    # Create a canvas object to write the PDF to
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)

    # Add the PDF title
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawCentredString(A4[0] / 2, A4[1] - 50, "My PDF Title")

    # Add the date created
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(50, A4[1] - 80, "Created on: " + str(datetime.datetime.now()))

    # Draw the PNG image on the PDF canvas
    pdf_canvas.drawImage(
        os.path.join(os.getcwd(), "static", "image.png"),
        x=50,
        y=A4[1] - 300,
        width=image.width / 2,
        height=image.height / 2,
        preserveAspectRatio=True,
        anchor="nw",
    )

    # Add some text below the graph
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(50, A4[1] - 500, "Some random text here...")

    # Close the PDF canvas to finalize the PDF file
    pdf_canvas.showPage()
    pdf_canvas.save()

    # Reset the buffer for reading
    buffer.seek(0)

    # Create a Django HttpResponse object with the PDF file data.
    response = FileResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="line_chart.pdf"'

    # Delete png image from the path
    png_path = os.path.join(os.getcwd(), "static", "image.png")
    image.close()
    os.remove(png_path)

    # Return the HttpResponse object containing the PDF file.
    return response


# For gauge data
@require_GET
def sensor_data_api(request):
    latest_data = SensorData.objects.latest("timestamp")
    data = {
        "timestamp": latest_data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": latest_data.temperature,
        "humidity": latest_data.humidity,
        "gas_value": latest_data.gas_value,
    }
    print(data)
    context = {
        "data": data,
    }
    return JsonResponse(data)


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect("newHome")
        else:
            messages.error(request, "Invalid credentials")
            return render(request, "login.html")
    else:
        return render(request, "login.html", {})


def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")

        user = User.objects.filter(username=username, email=email).first()

        if user:
            # generate a random password reset token
            token = "".join(random.choices(string.ascii_letters + string.digits, k=16))

            # set the token for the user and save the user
            user.profile.reset_token = token
            user.profile.save()

            # send the password reset email
            subject = "Password Reset Request"
            print(subject)
            message = f'Hello {user.first_name},\n\nYou have requested a password reset for your account.\n\nPlease click on the link below to reset your password:\n\n{request.build_absolute_uri("/")}?token={token}\n\nIf you did not request this reset, please ignore this email.\n\nBest regards,\nThe Sensor Data Team'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [
                email,
            ]
            send_mail(subject, message, from_email, recipient_list)

            return redirect("password_reset_done")
        else:
            # user not found, display error message
            messages.error(request, "Username and email do not match.")
            error_message = "Username and email do not match."
            print(error_message)
            return render(
                request, "forgot_password.html", {"error_message": error_message}
            )

    return render(request, "forgot_password.html")


def password_reset_done(request):
    return render(request, "password_reset_done.html")


def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("login_user")


@login_required(login_url=login_user)
def newHome(request):
    latest_temperature = SensorData.objects.latest("timestamp").temperature
    latest_humidity = SensorData.objects.latest("timestamp").humidity
    latest_gas = SensorData.objects.latest("timestamp").gas_value
    critical_temp = settings.CRITICAL_TEMP
    critical_hum = settings.CRITICAL_HUMIDITY
    critical_gas = settings.CRITICAL_GAS_VALUE
    average_temperature = 30.0
    sensor_data = SensorData.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by("timestamp")
    temperatures = [data.temperature for data in sensor_data]
    humidity_values = [data.humidity for data in sensor_data]
    gas_values = [data.gas_value for data in sensor_data]

    # Calculate highest and lowest temperatures
    filtered_temperatures = [t for t in temperatures if t is not None]
    average_temperature = sum(filtered_temperatures) / len(filtered_temperatures)
    highest_temp = max(filtered_temperatures)
    lowest_temp = min(filtered_temperatures)

    # Calculate highest and lowest humidity values
    filtered_humidity_values = [t for t in humidity_values if t is not None]
    average_humidity = sum(filtered_humidity_values) / len(filtered_humidity_values)
    highest_hum = max(filtered_humidity_values)
    lowest_hum = min(filtered_humidity_values)

    # Calculate highest and lowest gas values
    filtered_gas_values = [t for t in gas_values if t is not None]
    average_gas = sum(filtered_gas_values) / len(filtered_gas_values)
    highest_gas = max(filtered_gas_values)
    lowest_gas = min(filtered_gas_values)

    context = {
        "highest_temp": highest_temp,
        "lowest_temp": lowest_temp,
        "average_temperature": round(average_temperature, 1),
        "highest_hum": highest_hum,
        "lowest_hum": lowest_hum,
        "average_humidity": round(average_humidity, 1),
        "highest_gas": highest_gas,
        "lowest_gas": lowest_gas,
        "average_gas": round(average_gas, 1),
        "critical_temp": critical_temp,
        "critical_hum": critical_hum,
        "critical_gas": critical_gas,
        "latest_temperature": latest_temperature,
        "latest_humidity": latest_humidity,
        "latest_gas": latest_gas,
    }
    # print(context)
    return render(request, "newHome.html", context)


@login_required(login_url=login_user)
def testHome(request):
    # messages.success(request, f'Welcome {request.user.username}!')
    # send_mail(
    #     "Test mail",
    #     "Here is the message.",
    #     "anuman.1@iitj.ac.in",
    #     ["anuman23840@gmail.com"],
    #     fail_silently=False,
    # )

    if request.method == "POST":
        hour_data = request.POST.get("hour_data")
        minute_data = request.POST.get("minute_data")
        print(hour_data)
        print(minute_data)

    critical_temp = settings.CRITICAL_TEMP
    critical_hum = settings.CRITICAL_HUMIDITY
    critical_gas = settings.CRITICAL_GAS_VALUE
    average_temperature = 30.0
    sensor_data = SensorData.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by("timestamp")
    temperatures = [data.temperature for data in sensor_data]
    humidity_values = [data.humidity for data in sensor_data]
    gas_values = [data.gas_value for data in sensor_data]

    # Calculate highest and lowest temperatures
    filtered_temperatures = [t for t in temperatures if t is not None]
    average_temperature = sum(filtered_temperatures) / len(filtered_temperatures)
    highest_temp = max(filtered_temperatures)
    lowest_temp = min(filtered_temperatures)

    # Calculate highest and lowest humidity values
    filtered_humidity_values = [t for t in humidity_values if t is not None]
    average_humidity = sum(filtered_humidity_values) / len(filtered_humidity_values)
    highest_hum = max(filtered_humidity_values)
    lowest_hum = min(filtered_humidity_values)

    # Calculate highest and lowest gas values
    filtered_gas_values = [t for t in gas_values if t is not None]
    average_gas = sum(filtered_gas_values) / len(filtered_gas_values)
    highest_gas = max(filtered_gas_values)
    lowest_gas = min(filtered_gas_values)

    context = {
        "highest_temp": highest_temp,
        "lowest_temp": lowest_temp,
        "average_temperature": round(average_temperature, 1),
        "highest_hum": highest_hum,
        "lowest_hum": lowest_hum,
        "average_humidity": round(average_humidity, 1),
        "highest_gas": highest_gas,
        "lowest_gas": lowest_gas,
        "average_gas": round(average_gas, 1),
        "critical_temp": critical_temp,
        "critical_hum": critical_hum,
        "critical_gas": critical_gas,
    }
    # print(context)
    return render(request, "testHome.html", context)


@login_required(login_url=login_user)
def home(request):
    # messages.success(request, f'Welcome {request.user.username}!')
    # send_mail(
    #     "Test mail",
    #     "Here is the message.",
    #     "anuman.1@iitj.ac.in",
    #     ["anuman23840@gmail.com"],
    #     fail_silently=False,
    # )
    critical_temp = settings.CRITICAL_TEMP
    critical_hum = settings.CRITICAL_HUMIDITY
    critical_gas = settings.CRITICAL_GAS_VALUE
    average_temperature = 30.0
    sensor_data = SensorData.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by("timestamp")
    temperatures = [data.temperature for data in sensor_data]
    humidity_values = [data.humidity for data in sensor_data]
    gas_values = [data.gas_value for data in sensor_data]

    # Calculate highest and lowest temperatures
    filtered_temperatures = [t for t in temperatures if t is not None]
    average_temperature = sum(filtered_temperatures) / len(filtered_temperatures)
    highest_temp = max(filtered_temperatures)
    lowest_temp = min(filtered_temperatures)

    # Calculate highest and lowest humidity values
    filtered_humidity_values = [t for t in humidity_values if t is not None]
    average_humidity = sum(filtered_humidity_values) / len(filtered_humidity_values)
    highest_hum = max(filtered_humidity_values)
    lowest_hum = min(filtered_humidity_values)

    # Calculate highest and lowest gas values
    filtered_gas_values = [t for t in gas_values if t is not None]
    average_gas = sum(filtered_gas_values) / len(filtered_gas_values)
    highest_gas = max(filtered_gas_values)
    lowest_gas = min(filtered_gas_values)

    context = {
        "highest_temp": highest_temp,
        "lowest_temp": lowest_temp,
        "average_temperature": round(average_temperature, 1),
        "highest_hum": highest_hum,
        "lowest_hum": lowest_hum,
        "average_humidity": round(average_humidity, 1),
        "highest_gas": highest_gas,
        "lowest_gas": lowest_gas,
        "average_gas": round(average_gas, 1),
        "critical_temp": critical_temp,
        "critical_hum": critical_hum,
        "critical_gas": critical_gas,
    }
    # print(context)
    return render(request, "home.html", context)


@login_required
def profile(request):
    user = User.objects.get(pk=request.user.id)
    name = user.username[0]
    active_status = user.is_active
    staff_active_status = user.is_staff
    admin_active_status = user.is_superuser
    if active_status == True:
        status = "Active"
    else:
        status = "Not Active"

    if staff_active_status == True:
        staff_status = "Active"
    else:
        staff_status = "Not Active"

    if admin_active_status == True:
        admin_status = "Active"
    else:
        admin_status = "Not Active"

    link = "https://ui-avatars.com/api/?name=" + name
    context = {
        "name": name,
        "link": link,
        "user": user,
        "status": status,
        "staff_status": staff_status,
        "admin_status": admin_status,
    }
    print(link)
    return render(request, "profile.html", context)


# from datetime import datetime
import os


@login_required
def export_data(request):
    if request.method == "POST":
        start_date = request.POST.get("startDate")
        end_date = request.POST.get("endDate")
        # Convert start and end dates to datetime objects
        import datetime

        start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.datetime.strptime(
            end_date, "%Y-%m-%d"
        ) + datetime.timedelta(days=1)

        # sd = datetime.strptime(start_date, "%Y-%m-%d")
        # ed = datetime.strptime(end_date, "%Y-%m-%d")
        # print(sd)
        # print(end_date)
        if end_datetime <= start_datetime:
            messages.error(request, "End date must be ahead of start date.")
        else:
            # Get data from database between start and end dates
            data = SensorData.objects.filter(
                timestamp__range=[start_datetime, end_datetime]
            )

            # Create a list to hold the rows of the CSV file
            rows = [["Timestamp", "Temperature", "Humidity", "Gas Value"]]

            # Add data to the rows list
            for d in data:
                rows.append(
                    [
                        d.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        d.temperature,
                        d.humidity,
                        d.gas_value,
                    ]
                )

            # print(type(rows))

            data_dict = {
                "timestamps": [],
                "temperatures": [],
                "humidities": [],
                "gas_values": [],
            }
            latest_data = SensorData.objects.filter(
                timestamp__range=[start_datetime, end_datetime]
            )
            for edata in latest_data:
                data_dict["timestamps"].append(
                    edata.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )
                data_dict["temperatures"].append(edata.temperature)
                data_dict["humidities"].append(edata.humidity)
                data_dict["gas_values"].append(edata.gas_value)
            # print(data_dict)

            # write data to CSV file
            with open("sensor_data.csv", mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["timestamp", "temperature", "humidity", "gas_value"]
                )  # add column headers
                for i in range(len(data_dict["timestamps"])):
                    row = [
                        data_dict["timestamps"][i],
                        data_dict["temperatures"][i],
                        data_dict["humidities"][i],
                        data_dict["gas_values"][i],
                    ]
                    writer.writerow(row)

            from_email = settings.EMAIL_HOST_USER
            recipient_list = ["agrawal.14@iitj.ac.in", "anuman23840@gmail.com"]
            email = EmailMessage(
                "Exported Sensor Data",
                "Please find the exported sensor data attached.",
                from_email,
                recipient_list,
            )
            email.attach_file("sensor_data.csv")
            email.send()
            os.remove("sensor_data.csv")
            messages.success(request, "Data sent successfully!")

            # # Create a CSV file using the rows list
            # response = HttpResponse(content_type='text/csv')
            # response['Content-Disposition'] = f'attachment; filename="sensor_data_{start_date}_{end_date}.csv"'
            # writer = csv.writer(response)
            # writer.writerows(rows)

            # # Send the CSV file as an attachment via email
            # from_email = settings.EMAIL_HOST_USER
            # recipient_list = ["agrawal.14@iitj.ac.in", "anuman23840@gmail.com"]
            # body='Please find attached the CSV file with the sensor data.'
            # subject='Sensor Data'
            # email = EmailMessage(
            #     subject,
            #     body,
            #     from_email,
            #     recipient_list,
            # )
            # email.attach_file(response)
            # email.send()
            # messages.success(request, "Data sent successfully!")
            # return redirect("export_data")

    return render(request, "export_data.html")


@csrf_exempt
def getlivedata(request):
    if request.method == "POST":
        temperature = request.POST.get("temperature")
        humidity = request.POST.get("humidity")
        gas_value = request.POST.get("gas_value")
        # Save the data to the database
        data = SensorData.objects.create(
            temperature=temperature, humidity=humidity, gas_value=gas_value
        )
        data.save()
        return HttpResponse("Received and stored successfully")
    else:
        return HttpResponseBadRequest("Invalid request method")


# def get_initial_temperature_data(request):
#     # Query the SensorData model to get the last 10 temperature values
#     temperature_data = SensorData.objects.order_by('-timestamp')[:10]
#     # Create lists for the labels and values in the chart
#     labels = [data.timestamp.strftime('%H:%M:%S') for data in reversed(temperature_data)]
#     values = [data.value for data in reversed(temperature_data)]
#     # Create a dictionary containing the labels and values lists
#     data_dict = {'labels': labels, 'values': values}
#     # Return the data as a JSON response
#     return JsonResponse(data_dict)


# def get_temperature_data(request):
#     # Query the SensorData model to get the latest temperature value
#     latest_temperature = SensorData.objects.latest('timestamp').value
#     # Create a dictionary containing the label and value for the latest temperature value
#     data_dict = {'label': datetime.now().strftime('%H:%M:%S'), 'value': latest_temperature}
#     # Return the data as a JSON response
#     return JsonResponse(data_dict)


def get_initial_temperature_data(request):
    # Query the SensorData model to get the last 10 temperature values
    temperature_data = SensorData.objects.order_by("-timestamp")[:10].values(
        "temperature", "timestamp"
    )

    # Convert the timestamp values to the local timezone
    for data in temperature_data:
        data["timestamp"] = timezone.localtime(data["timestamp"])

    # Create lists for the labels and values in the chart
    labels = [
        data["timestamp"].strftime("%H:%M:%S") for data in reversed(temperature_data)
    ]
    values = [data["temperature"] for data in reversed(temperature_data)]

    # Create a dictionary containing the labels and values lists
    data_dict = {"labels": labels, "values": values}

    # Return the data as a JSON response
    return JsonResponse(data_dict)


def get_temperature_data(request):
    # Query the SensorData model to get the latest temperature value
    latest_temperature = SensorData.objects.latest("timestamp").temperature
    # Create a dictionary containing the label and value for the latest temperature value
    data_dict = {
        "label": datetime.now().strftime("%H:%M:%S"),
        "value": latest_temperature,
    }
    # Return the data as a JSON response
    # print(data_dict)
    return JsonResponse(data_dict)


def get_initial_humidity_data(request):
    # Query the SensorData model to get the last 10 temperature values
    humidity_data = SensorData.objects.order_by("-timestamp")[:10].values(
        "humidity", "timestamp"
    )
    # Convert the timestamp values to the local timezone
    for data in humidity_data:
        data["timestamp"] = timezone.localtime(data["timestamp"])

    # Create lists for the labels and values in the chart
    labels = [
        data["timestamp"].strftime("%H:%M:%S") for data in reversed(humidity_data)
    ]
    values = [data["humidity"] for data in reversed(humidity_data)]
    # Create a dictionary containing the labels and values lists
    data_dict = {"labels": labels, "values": values}
    # Return the data as a JSON response
    # print(data_dict)
    return JsonResponse(data_dict)


def get_humidity_data(request):
    # Query the SensorData model to get the latest temperature value
    latest_humidity = SensorData.objects.latest("timestamp").humidity
    # Create a dictionary containing the label and value for the latest temperature value
    data_dict = {"label": datetime.now().strftime("%H:%M:%S"), "value": latest_humidity}
    # Return the data as a JSON response
    # print(data_dict)
    return JsonResponse(data_dict)


def get_initial_gas_data(request):
    # Query the SensorData model to get the last 10 temperature values
    gas_data = SensorData.objects.order_by("-timestamp")[:10].values(
        "gas_value", "timestamp"
    )
    # temperature_data = SensorData.objects.latest('temperature')[:10]

    # Convert the timestamp values to the local timezone
    for data in gas_data:
        data["timestamp"] = timezone.localtime(data["timestamp"])

    # Create lists for the labels and values in the chart
    labels = [data["timestamp"].strftime("%H:%M:%S") for data in reversed(gas_data)]
    values = [data["gas_value"] for data in reversed(gas_data)]
    # Create a dictionary containing the labels and values lists
    data_dict = {"labels": labels, "values": values}
    # Return the data as a JSON response
    # print(data_dict)
    return JsonResponse(data_dict)


def get_gas_data(request):
    # Query the SensorData model to get the latest temperature value
    latest_gas = SensorData.objects.latest("timestamp").gas_value
    # Create a dictionary containing the label and value for the latest temperature value
    data_dict = {"label": datetime.now().strftime("%H:%M:%S"), "value": latest_gas}
    # Return the data as a JSON response
    # print(data_dict)
    return JsonResponse(data_dict)


def temperature_range_today(request):
    # Get the current date
    today = timezone.now().date()

    # Get the lowest and highest temperature value for today
    temperature_range = SensorData.objects.filter(timestamp__date=today).aggregate(
        lowest_temperature=Min("temperature"), highest_temperature=Max("temperature")
    )
    # print(temperature_range)
    # print(type(temperature_range))

    # Return the temperature range as JSON
    return JsonResponse(temperature_range)


import csv
import json
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from datetime import date, timedelta
from django.core import serializers

# from home.models import SensorData
from django.core.mail import EmailMessage


def data_to_json(request):
    latest_data = SensorData.objects.order_by("-timestamp")[:20]
    data_dict = {
        "timestamps": [],
        "temperatures": [],
        "humidities": [],
        "gas_values": [],
    }
    for data in latest_data:
        data_dict["timestamps"].append(data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        data_dict["temperatures"].append(data.temperature)
        data_dict["humidities"].append(data.humidity)
        data_dict["gas_values"].append(data.gas_value)
    print(data_dict)
    # write data to CSV file
    with open("sensor_data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["timestamp", "temperature", "humidity", "gas_value"]
        )  # add column headers
        for i in range(len(data_dict["timestamps"])):
            row = [
                data_dict["timestamps"][i],
                data_dict["temperatures"][i],
                data_dict["humidities"][i],
                data_dict["gas_values"][i],
            ]
            writer.writerow(row)

    from_email = settings.EMAIL_HOST_USER
    recipient_list = ["agrawal.14@iitj.ac.in", "anuman23840@gmail.com"]
    email = EmailMessage(
        "Latest Sensor Data",
        "Please find the latest sensor data attached.",
        from_email,
        recipient_list,
    )
    email.attach_file("sensor_data.csv")
    email.send()
    return JsonResponse(data_dict)
