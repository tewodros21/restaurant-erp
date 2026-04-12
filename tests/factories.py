import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth import get_user_model
from accounts.models import Branch
from menu.models import Menu, MenuSection, MenuItem
from tables.models import Table, TableSeat, SeatingArrangement
from inventory.models import Ingredient, Unit, Category, Recipe, RecipeIngredient
from pos.models import Order, Meal, MealItem

fake = Faker()
User = get_user_model()


class BranchFactory(DjangoModelFactory):
    class Meta:
        model = Branch

    name    = factory.LazyFunction(lambda: fake.company())
    address = factory.LazyFunction(lambda: fake.address())
    phone   = factory.LazyFunction(lambda: fake.phone_number()[:20])


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username   = factory.LazyFunction(lambda: fake.user_name())
    email      = factory.LazyFunction(lambda: fake.email())
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name  = factory.LazyFunction(lambda: fake.last_name())
    password   = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role       = 'WAITER'
    branch     = factory.SubFactory(BranchFactory)


class MenuFactory(DjangoModelFactory):
    class Meta:
        model = Menu

    branch = factory.SubFactory(BranchFactory)
    name   = 'Main Menu'


class MenuSectionFactory(DjangoModelFactory):
    class Meta:
        model = MenuSection

    menu  = factory.SubFactory(MenuFactory)
    name  = factory.LazyFunction(lambda: fake.word())
    order = factory.Sequence(lambda n: n)


class MenuItemFactory(DjangoModelFactory):
    class Meta:
        model = MenuItem

    section          = factory.SubFactory(MenuSectionFactory)
    name             = factory.LazyFunction(lambda: fake.word())
    price            = factory.LazyFunction(lambda: fake.pydecimal(left_digits=3, right_digits=2, positive=True))
    category         = 'FOOD'
    is_available     = True
    preparation_time = 15


class TableFactory(DjangoModelFactory):
    class Meta:
        model = Table

    branch       = factory.SubFactory(BranchFactory)
    table_number = factory.Sequence(lambda n: f'T{n}')
    capacity     = 4
    status       = 'AVAILABLE'


class UnitFactory(DjangoModelFactory):
    class Meta:
        model = Unit

    name         = 'Kilogram'
    abbreviation = 'kg'


class IngredientCategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.LazyFunction(lambda: fake.word())


class IngredientFactory(DjangoModelFactory):
    class Meta:
        model = Ingredient

    branch        = factory.SubFactory(BranchFactory)
    category      = factory.SubFactory(IngredientCategoryFactory)
    unit          = factory.SubFactory(UnitFactory)
    name          = factory.LazyFunction(lambda: fake.word())
    current_stock = 100
    minimum_stock = 10
    cost_per_unit = 5


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    branch     = factory.SubFactory(BranchFactory)
    table      = factory.SubFactory(TableFactory)
    waiter     = factory.SubFactory(UserFactory)
    order_type = 'DINE_IN'
    status     = 'PENDING'