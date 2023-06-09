from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path("newHome/", views.newHome, name="newHome"),
    path("testHome/", views.testHome, name="testHome"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),
    path("getlivedata/", views.getlivedata, name="getlivedata"),
    path(
        "get_initial_temperature_data/",
        views.get_initial_temperature_data,
        name="get_initial_temperature_data",
    ),
    path(
        "get_temperature_data/", views.get_temperature_data, name="get_temperature_data"
    ),
    path(
        "get_initial_humidity_data/",
        views.get_initial_humidity_data,
        name="get_initial_humidity_data",
    ),
    path("get_humidity_data/", views.get_humidity_data, name="get_humidity_data"),
    path(
        "get_initial_gas_data/", views.get_initial_gas_data, name="get_initial_gas_data"
    ),
    path("get_gas_data/", views.get_gas_data, name="get_gas_data"),
    path(
        "temperature_range_today/",
        views.temperature_range_today,
        name="temperature_range_today",
    ),
    path("profile/", views.profile, name="profile"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("password_reset_done/", views.password_reset_done, name="password_reset_done"),
    path("data_to_json", views.data_to_json, name="data_to_json"),
    path("export_data/", views.export_data, name="export_data"),
    path("sensor-data/", views.sensor_data_api, name="sensor-data-api"),
    path("line-chart/", views.line_chart_view, name="line_chart"),
    path("sensor-data-api/", views.sensor_data_api2, name="sensor-data-api2"),
]
