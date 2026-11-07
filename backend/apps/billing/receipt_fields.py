"""Receipt fields showing how a payment was split between charges and deposit."""

from rest_framework import serializers


class AllocationFields(serializers.Serializer):
    """How a receipt was split, and the deposit now held when one was paid."""

    allocation = serializers.SerializerMethodField()
    deposit_held = serializers.SerializerMethodField()

    def get_allocation(self, obj):
        from .deposits import allocation

        if not hasattr(obj, "_allocation"):
            obj._allocation = allocation(obj)
        return obj._allocation

    def get_deposit_held(self, obj):
        from .deposits import held

        rows = self.get_allocation(obj)
        if not obj.invoice.lease_id or not any(row["kind"] == "deposit" for row in rows):
            return None
        return f"{held(obj.invoice.lease):.2f}"
