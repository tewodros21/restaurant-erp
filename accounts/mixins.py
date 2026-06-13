class BranchScopedQuerysetMixin:
    """Scope a generic view's queryset to the requesting user's branch.

    This closes the cross-branch IDOR class where detail views used an
    unscoped ``queryset = Model.objects.all()`` and let any authorized user
    read/modify another branch's object by guessing its id.

    Behaviour:
      * ADMIN sees every branch (full system access per the RBAC spec).
      * Any other role sees only objects whose branch matches their own.
      * A user with no branch sees nothing (``none()``).

    Set ``branch_lookup`` to the ORM path from the model to its Branch when it
    isn't a direct ``branch`` field (e.g. ``'asset__branch'``).
    """
    branch_lookup = 'branch'

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, 'user', None)

        if getattr(user, 'role', None) == 'ADMIN':
            return qs

        branch = getattr(user, 'branch', None)
        if branch is None:
            return qs.none()
        return qs.filter(**{self.branch_lookup: branch})
