from rest_framework import status
from rest_framework.response import Response
from rest_framework_jwt.views import BaseJSONWebTokenAPIView

from rbaca.api.serializers import ExpandedTokenVerification


class VerifyNodeAcces(BaseJSONWebTokenAPIView):
    """
    Custom view for verifying node access using JWT tokens.

    This view extends the BaseJSONWebTokenAPIView to provide custom token verification.
    It checks the validity of the token and verifies node access.

    Note:
        Ensure that the 'serializer_class' is set to 'ExpandedTokenVerification'
        for this view to handle token verification with additional node access checks.

    To use this view, make a POST request with a valid token and the 'node' parameter
    specifying the node you want to access. The view will return a 200 OK response
    if the token is valid and has access to the node. If the token is invalid or does
    not have access, it will return a 403 Forbidden response with error details.
    """

    serializer_class = ExpandedTokenVerification

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for verifying node access.

        This method checks the validity of the JWT token and ensures that the user has
        access to the requested node.

        Args:
            request (HttpRequest): The HTTP request containing the token and 'node' parameter.

        Returns:
            Response (HttpResponse): A response indicating the result of token verification.
            If successful, it returns a 200 OK response; otherwise, a 403 Forbidden
            response with error details.

        Example:
            ```
            POST /verify_node_access/ (with 'token' and 'node' parameters)
            ```
        """
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            return super().post(request, *args, **kwargs)

        return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
