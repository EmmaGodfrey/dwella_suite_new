from django.http import HttpResponseNotFound


def deny_public_identity_document(request, filename):
    # Identity files are delivered only through the authenticated staff API.
    return HttpResponseNotFound()
