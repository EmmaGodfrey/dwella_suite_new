from django.db.models.functions import Length


def next_reference(organization, model, prefix, field="reference"):
    """Return the next `<PREFIX>-0001` style number for `model` in `organization`.

    Call inside a transaction: locking the organization row serialises
    allocation, so two records created at once cannot take the same number.
    The database finds the highest number (longest, then greatest), so the cost
    does not grow with the workspace's history.
    """
    from apps.organizations.models import Organization

    Organization.objects.select_for_update().get(pk=organization.pk)
    latest = (
        model.objects.filter(organization=organization, **{f"{field}__regex": rf"^{prefix}-\d+$"})
        .order_by(Length(field).desc(), f"-{field}")
        .values_list(field, flat=True)
        .first()
    )
    number = int(latest.rsplit("-", 1)[-1]) if latest else 0
    return f"{prefix}-{number + 1:04d}"
