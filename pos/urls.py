from django.urls import path
from . import views

urlpatterns = [
    # Orders
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/create/', views.CreateOrderView.as_view(), name='create-order'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/submit/', views.SubmitOrderView.as_view(), name='submit-order'),
    path('orders/<int:order_id>/status/', views.UpdateOrderStatusView.as_view(), name='update-order-status'),

    # Meals
    path('orders/<int:order_id>/meals/', views.AddMealView.as_view(), name='add-meal'),
    path('meals/<int:meal_id>/items/', views.AddMealItemView.as_view(), name='add-meal-item'),
    path('items/<int:item_id>/status/', views.UpdateMealItemStatusView.as_view(), name='update-item-status'),

    # KOT / BOT
    path('kot/', views.KOTListView.as_view(), name='kot-list'),
    path('bot/', views.BOTListView.as_view(), name='bot-list'),

    # Reservations
    path('reservations/', views.ReservationListView.as_view(), name='reservation-list'),
    path('reservations/available/', views.AvailableTablesForReservationView.as_view(), name='reservation-available-tables'),
    path('reservations/<int:pk>/', views.ReservationDetailView.as_view(), name='reservation-detail'),
    path('reservations/<int:pk>/cancel/', views.CancelReservationView.as_view(), name='reservation-cancel'),
    path('reservations/<int:pk>/check-in/', views.CheckInReservationView.as_view(), name='reservation-check-in'),

    # Billing & Payments
    path('orders/<int:order_id>/bill/', views.GenerateBillView.as_view(), name='generate-bill'),
    path('bills/<int:pk>/', views.BillDetailView.as_view(), name='bill-detail'),
    path('bills/<int:bill_id>/pay/', views.ProcessPaymentView.as_view(), name='process-payment'),
]

