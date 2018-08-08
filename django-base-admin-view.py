"""Base Admin View in Django that handles common validations and operations."""

from abc import abstractmethod

from base.exceptions import ModelOperationError, PermissionDeniedError, RequestValidationError

from django.contrib import messages
from django.shortcuts import render
from django.views import View
from django.views.defaults import ERROR_400_TEMPLATE_NAME


class AbstractAdminView(View):
    """Base AdminView for Admin related pages."""

    client_exceptions = (RequestValidationError, PermissionDeniedError,)
    server_exceptions = (ModelOperationError,)

    @property
    @abstractmethod
    def template_path(self):
        raise NotImplementedError('Please implement template path!')

    def _validate_required_fields(self, request):
        method = request.method
        try:
            keys = getattr(self, '{}_fields'.format(method.lower()))
        except AttributeError:
            keys = None
        if not keys:
            return
        data = getattr(request, method).dict()
        missing_keys = []
        for key in keys:
            if not data.get(key):
                missing_keys.append(key)
        if not missing_keys:
            return
        raise RequestValidationError('Error: Missing values for {}.'.format(
            ', '.join(str(e) for e in missing_keys)))

    def dispatch(self, request, *args, **kwargs):
        try:
            self._validate_required_fields(request)
            return super().dispatch(request, *args, **kwargs)
        except self.client_exceptions as e:
            error_msg = e.args[0]
            messages.add_message(request, messages.ERROR, error_msg)
            context = {
                'status': 'Bad Request(400)',
                'msg': error_msg
            }
            return self.render_view(
                request, ERROR_400_TEMPLATE_NAME, context=context)

    def render_view(
            self, request, template_path=None, context=None,
            content_type='text/html'):
        if not template_path:
            template_path = self.template_path
        return render(request, template_path, context, content_type)
