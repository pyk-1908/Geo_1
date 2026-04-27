import json
import logging
import os
from typing import Optional

import pyotp
from django.http import HttpRequest, JsonResponse
from ninja import Schema
from ninja.throttling import AnonRateThrottle, UserRateThrottle
from ninja_extra import NinjaExtraAPI, api_controller, http_post
from ninja_extra.exceptions import Throttled
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController, schema
from ninja_jwt.exceptions import AuthenticationFailed, InvalidToken

from siapp.models import OtpSecrets
from siapp.views.buyer_view.api import router_buyer
from siapp.views.lists.api import router_lists
from siapp.views.upload.api import router_upload

logger = logging.getLogger('django')


@api_controller("/token")
class AuthController(NinjaJWTDefaultController):
    class otp_schema(schema.obtain_pair_schema):
        otp: Optional[str] = None

    @http_post(
        "/pair",
        response=schema.obtain_pair_schema.get_response_schema(),
        url_name="token_obtain_pair",
    )
    def obtain_token(self, user_token: otp_schema, request: HttpRequest):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        user = user_token._user
        if user_token.otp is None:
            if OtpSecrets.objects.filter(user=user.id).exists():
                otp_secret = OtpSecrets.objects.get(user=user.id)
                if otp_secret.active:
                    return JsonResponse({"message": "OTP needed"}, status=403)
        else:
            if OtpSecrets.objects.filter(user=user.id).exists():
                otp_secret = OtpSecrets.objects.get(user=user.id)
                if otp_secret.active:
                    totp = pyotp.TOTP(otp_secret.secret)
                    if not totp.verify(user_token.otp):
                        return JsonResponse({"message": "Invalid OTP"}, status=401)

        logger.info(f"Successful login from IP:{ip} for USER:{user_token.username}")
        token_response = super().obtain_token(user_token)
        return token_response

    @http_post(
        "/refresh",
        response=schema.obtain_pair_refresh_schema.get_response_schema(),
        url_name="token_refresh",
    )
    def refresh_token(self, refresh_token: schema.obtain_pair_refresh_schema):
        return super().refresh_token(refresh_token)


throttle = []
if os.getenv("ENV") != "TEST":
    throttle += [
        AnonRateThrottle('50/m'),
        UserRateThrottle('10000/m'),
    ]

api = NinjaExtraAPI(throttle=throttle, csrf=False)
api.register_controllers(AuthController)
api.add_router("/buyer/", router_buyer)
api.add_router("/lists/", router_lists)
api.add_router("/upload/", router_upload)


@api.exception_handler(Throttled)
def handle_throttled(request, exc):
    return api.create_response(
        request,
        {"message": "Too many requests, please retry later"},
        status=429,
    )


@api.exception_handler(AuthenticationFailed)
def handle_authentication_failed(request, exc):
    if isinstance(exc, InvalidToken):
        return api.create_response(request, exc.detail, status=401)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    try:
        payload = json.loads(request.body)
        username = payload["username"]
    except json.JSONDecodeError:
        username = "Unknown (Invalid JSON)"
    logger.warning(f"Failed login attempt from IP:{ip} for USER:{username}")
    return api.create_response(request, {"message": "Authentication Failed"}, status=401)
