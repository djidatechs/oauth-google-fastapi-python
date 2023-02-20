from fastapi import APIRouter, Body, Depends
import requests
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from db import  get_db
from .high import User

router = APIRouter()

@router.post("/google-oauth")
async def google_oauth(data: dict = Body(...), db: Session = Depends(get_db)):
    # Get authorization code from request body
    code = data.get("code")

    # Request access token from Google API using the authorization code
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "YOUR_REDIRECT_URI",
            "grant_type": "authorization_code",
        },
    )
    access_token = response.json().get("access_token", None)

    # Fetch user information from Google API using the access token
    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_info = response.json()
    email = user_info.get("email", None)

    # Check if user exists in the database
    user = db.query(User).filter(User.email == email).first()

    if user is not None:
        # Add role to user_info if user exists in the database
        user_info["role"] = user.role
    else:
        # Create a new user if user does not exist in the database
        user_info["role"] = "user"
        if email is not None:
            user = User(email=email)
            db.add(user)
            db.commit()

    # Return access_token and user_info as JSONResponse
    return JSONResponse(content={"access_token": access_token, "user_info": user_info})
