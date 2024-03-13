import traceback
from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from sqlalchemy import func
from typing import List,Optional
from .. import models,schemas,utils
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

redis_client = redis.Redis(host='51.20.142.197', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds


@router.get('',status_code=status.HTTP_202_ACCEPTED)
def users(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_users = redis_client.get("users")
    if cached_users:
        # If found in the cache, decode the JSON and return the cached data
        users_dict = json.loads(cached_users)

        # Check if products are still in the database
        with db as session:
            users_in_db = session.query(models.User).all()

        if not users_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("users")

            return []
    else:
        with db as session:
            try:
                users = session.query(models.User).all()
                users_dict = [user.to_dict() for user in users]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("users", cache_ttl, json.dumps(users_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return users_dict



@router.post('',status_code=status.HTTP_201_CREATED)
def upload_user(request: schemas.UserUpload, db: Session = Depends(get_db_write)):
    with db as session:
        try:

            hashed_password = utils.hash(request.password)
            request.password = hashed_password

            verification_token = utils.generate_verification_token()

            new_user = models.User(**request.dict(), verification_token=verification_token)

            session.add(new_user)

            session.commit()
            session.refresh(new_user)

            redis_client.delete("users")

            utils.send_verification_email(new_user.email, verification_token)

            return {"message": "Verification link sent to your email. Please check your inbox."}

            # Clear the "products" cache after a new product is added
        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)


@router.get('/verify-email/{verification_token}', status_code=status.HTTP_200_OK)
def verify_email(verification_token: str, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Find the user with the given verification token
            user = session.query(models.User).filter(models.User.verification_token == verification_token).first()

            if user:
                # Mark the user as verified in the database
                user.is_verified = True
                session.commit()

                # Clear the "users" cache after a new user is added
                redis_client.delete("users")

                return {"message": "Email verified successfully. You can now log in."}
            else:
                raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            session.rollback()
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error verifying email: {str(e)}")


@router.get('/{id}',status_code=status.HTTP_202_ACCEPTED)
def get_user(id: int, db: Session = Depends(get_db_read)):
    with db as session:
        try:
            # Try to retrieve the data from Redis cache
            cache_key = f'users:{id}'
            cached_user = redis_client.get(cache_key)
            if cached_user:
                return json.loads(cached_user)

            # If not in cache, query the database
            user = session.query(models.User).filter(models.User.id == id).first()

            if user:
                # Convert the project object to a dictionary
                user_data = user.to_dict()

                # Cache the data in Redis with the specified TTL
                redis_client.setex(cache_key, cache_ttl, json.dumps(user_data))

                return user_data
            else:
                raise HTTPException(status_code=404, detail="User not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        



@router.put('/{id}',status_code=status.HTTP_200_OK)
def update_user(id: int, updated_user: schemas.UserUpload, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            user_query = session.query(models.User).filter(models.User.id == id)
            user = user_query.first()

            if user:
                # Update the product in the database
                hashed_password = utils.hash(updated_user.password)  # Fix this line
                updated_user.password = hashed_password
                
                user_query.update(updated_user.dict(), synchronize_session=False)
                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                return user_query.first()

            else:
                raise HTTPException(status_code=404, detail="User not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")

        


@router.delete('/{id}',status_code=status.HTTP_200_OK)
def delete_user(id: int,db: Session = Depends(get_db_write)):

    with db as session:
        try:
            delete_user = session.query(models.User).filter(models.User.id == id)
            delete_user.delete(synchronize_session=False)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")