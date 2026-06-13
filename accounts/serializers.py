from rest_framework import serializers
from .models import User, Branch


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    # Privileged fields — only an ADMIN may change these (see validate()).
    PRIVILEGED_FIELDS = ('role', 'branch', 'is_active')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'branch', 'branch_name', 'phone', 'is_active'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """Prevent privilege escalation: non-admins cannot change role/branch/active."""
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        is_admin = bool(actor and getattr(actor, 'role', None) == 'ADMIN')

        if not is_admin and self.instance is not None:
            for field in self.PRIVILEGED_FIELDS:
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError(
                        {field: 'Only an administrator can change this field.'}
                    )
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name',
                  'last_name', 'role', 'branch', 'phone']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user