from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Menu, MenuSection, MenuItem
from .serializers import MenuSerializer, MenuSectionSerializer, MenuItemSerializer
from accounts.permissions import IsManager, IsWaiter


class MenuDetailView(generics.RetrieveAPIView):
    """Get full menu for a branch"""
    serializer_class = MenuSerializer
    permission_classes = [IsWaiter]

    def get_object(self):
        branch = self.request.user.branch
        return Menu.objects.get(branch=branch)


class MenuSectionListView(generics.ListCreateAPIView):
    serializer_class = MenuSectionSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MenuSection.objects.filter(
            menu__branch=self.request.user.branch
        )


class MenuSectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuSectionSerializer
    permission_classes = [IsManager]
    queryset = MenuSection.objects.all()


class MenuItemListView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MenuItem.objects.filter(
            section__menu__branch=self.request.user.branch
        )


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]
    queryset = MenuItem.objects.all()


class PublicMenuView(generics.RetrieveAPIView):
    """Public view for QR menu - no auth required"""
    serializer_class = MenuSerializer
    permission_classes = []

    def get_object(self):
        branch_id = self.kwargs['branch_id']
        return Menu.objects.get(branch_id=branch_id)