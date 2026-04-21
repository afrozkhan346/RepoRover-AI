from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError

from app.db.session import SessionLocal
from app.core.config import settings
from app.services.auth_service import handle_social_login

router = APIRouter()

oauth = OAuth()

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.github_client_id and settings.github_client_secret:
    oauth.register(
        name="github",
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{provider}/login")
async def login(request: Request, provider: str):
    if provider not in ["google", "github"]:
        raise HTTPException(status_code=404, detail="Provider not found")

    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(
            status_code=400,
            detail=f"{provider.capitalize()} OAuth is not configured. Please add its Client ID and Secret to your backend .env.",
        )

    redirect_uri = str(request.url_for("auth_callback", provider=provider))
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def auth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    if provider not in ["google", "github"]:
        raise HTTPException(status_code=404, detail="Provider not found")

    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail=f"{provider} OAuth is not configured")

    try:
        token = await client.authorize_access_token(request)
    except OAuthError as e:
        print(f"OAuth error for {provider}:", e)
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=access_denied")

    if provider == "google":
        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=400, detail="Could not fetch user info from Google")
        email = user_info.get("email")
        name = user_info.get("name")
        image = user_info.get("picture")
        account_id = str(user_info.get("sub"))
    elif provider == "github":
        resp = await client.get("user", token=token)
        profile = resp.json()
        account_id = str(profile.get("id"))
        name = profile.get("name") or profile.get("login")
        image = profile.get("avatar_url")
        email = profile.get("email")

        if not email:
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            for e in emails:
                if e.get("primary"):
                    email = e.get("email")
                    break
            if not email and emails:
                email = emails[0].get("email")
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not email:
        raise HTTPException(status_code=400, detail="No email address provided by OAuth provider")

    auth_result = handle_social_login(
        db=db,
        provider_id=provider,
        account_id=account_id,
        email=email,
        name=name or email.split('@')[0],
        image=image,
    )

    redirect_url = f"{settings.frontend_url}/auth/callback?token={auth_result.token}&new={str(auth_result.is_new).lower()}"
    return RedirectResponse(url=redirect_url)
