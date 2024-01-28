from jose import JWTError,jwt
from datetime import datetime,timedelta
from pydantic import EmailStr
from . import schemas,database,models
from fastapi import Depends,status,HTTPException,Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# Constants
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Token creation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token verification
def verify_access_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Dependency for getting current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db_read)):
    user_id = verify_access_token(token, db)
    # Retrieve user data from the database using user_id
    user = db.query(models.User).get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# Adding a dependency Function

def verify_user(current_user: models.User = Depends(get_current_user)):

    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")
    return {"message": "You are verified"}