from litestar.security.jwt import JWTCookieAuth, Token
from litestar.connection import ASGIConnection

SECRET = "jhsdfitw76TY62TGD2tr65rF5d45565r"


async def retrieve_user_handler(token: Token, connection: ASGIConnection) -> dict:
    return {"user_id": token.sub, "admin": token.extras.get("admin")}


jwt_cookie_auth = JWTCookieAuth(
    token_secret=SECRET,
    retrieve_user_handler=retrieve_user_handler,
    exclude_opt_key="exclude_from_auth",
    exclude=[
        "/login",
        "/schema",
    ],
)
