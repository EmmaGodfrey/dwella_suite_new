from .models import AuditEvent


def record_event(request, action, resource=None, organization=None, **metadata):
    session = getattr(request, "support_session", None)
    if session:
        metadata.setdefault("support_session", str(session.public_id))
        metadata.setdefault("reason", session.reason)
    user = request.user
    return AuditEvent.objects.create(
        actor=user if user.is_authenticated else None,
        organization=organization or getattr(request, "organization", None),
        action=action,
        resource_type=resource._meta.label_lower if resource is not None else "",
        resource_id=str(getattr(resource, "public_id", resource.pk))
        if resource is not None
        else "",
        request_id=getattr(request, "request_id", "")[:120],
        metadata=metadata,
    )
