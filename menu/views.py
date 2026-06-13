from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Menu, MenuSection, MenuItem
from .serializers import MenuSerializer, MenuSectionSerializer, MenuItemSerializer
from accounts.permissions import IsManager, IsWaiter
from accounts.mixins import BranchScopedQuerysetMixin


class MenuDetailView(generics.RetrieveAPIView):
    """Get full menu for a branch"""
    serializer_class = MenuSerializer
    permission_classes = [IsWaiter]

    def get_object(self):
        branch = self.request.user.branch
        menu, created = Menu.objects.get_or_create(
            branch=branch,
            defaults={'name': f"{branch.name} Menu"}
        )
        return menu


class MenuSectionListView(generics.ListCreateAPIView):
    serializer_class = MenuSectionSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MenuSection.objects.filter(
            menu__branch=self.request.user.branch
        )


class MenuSectionDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuSectionSerializer
    permission_classes = [IsManager]
    queryset = MenuSection.objects.all()
    branch_lookup = 'menu__branch'


class MenuItemListView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        return MenuItem.objects.filter(
            section__menu__branch=self.request.user.branch
        )


class MenuItemDetailView(BranchScopedQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsManager]
    queryset = MenuItem.objects.all()
    branch_lookup = 'section__menu__branch'


class PublicMenuView(generics.RetrieveAPIView):
    """Public view for QR menu - no auth required"""
    serializer_class = MenuSerializer
    permission_classes = []

    def get_object(self):
        branch_id = self.kwargs['branch_id']
        return get_object_or_404(Menu, branch_id=branch_id, is_active=True)