def next_reference(organization, model, prefix, field="reference"):
    """Return the next `<PREFIX>-0001` style number for `model` in `organization`.

    Call inside a transaction: locking the organization row serialises
    allocation, so two records created at once cannot take the same number.
    """
    from apps.organizations.models import Organization

    Organization.objects.select_for_update().get(pk=organization.pk)
    references = model.objects.filter(organization=organization).values_list(field, flat=True)
    numbers = (
        int(ref.rsplit("-", 1)[-1]) for ref in references if ref.rsplit("-", 1)[-1].isdigit()
    )
    return f"{prefix}-{max(numbers, default=0) + 1:04d}"
