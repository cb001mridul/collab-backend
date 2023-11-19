from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from sqlalchemy import func
from typing import List,Optional
from .. import models,schemas
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import traceback

router = APIRouter(
    prefix='/padmins',
    tags=['Project Admins']
)

redis_client = redis.Redis(host='13.51.235.207', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds


# Endpoints for getting project admins..
@router.get('',status_code=status.HTTP_202_ACCEPTED)
def admins(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_admins = redis_client.get("padmin")
    if cached_admins:
        # If found in the cache, decode the JSON and return the cached data
        admins_dict = json.loads(cached_admins)

        # Check if products are still in the database
        with db as session:
            admins_in_db = session.query(models.ProjectAdmin).all()

        if not admins_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("padmin")

            return []
    else:
        with db as session:
            try:
                admins = session.query(models.ProjectAdmin).all()
                admins_dict = [admin.to_dict() for admin in admins]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("padmin", cache_ttl, json.dumps(admins_dict))
            except SQLAlchemyError as e:
                session.rollback()
                error_message = f"Database error: {str(e)}"
                traceback.print_exc()  # Print the traceback for debugging purposes
                raise HTTPException(status_code=500, detail=error_message)

    return admins_dict




@router.post('', status_code=status.HTTP_201_CREATED)
def upload_admin(request: schemas.UploadAdmin, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Convert Pydantic model to dictionary for ProjectAdmin creation
            admin_data = request.dict()

            # Extract educations and experiences from request
            educations_data = admin_data.pop("educations", [])
            experiences_data = admin_data.pop("experiences", [])

            # Create a new ProjectAdmin instance
            new_admin = models.ProjectAdmin(**admin_data)

            # Add experiences and educations
            for experience_data in experiences_data:
                new_experience = models.Experience(**experience_data)  # Use the dictionary as it is
                new_admin.experiences.append(new_experience)
            
            for education_data in educations_data:
                new_education = models.Education(**education_data)  # Use the dictionary as it is
                new_admin.educations.append(new_education)

            # Add the new admin to the session
            session.add(new_admin)
            session.commit()
            session.refresh(new_admin)

            # Clear the cache
            redis_client.delete("padmin")

            return request

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)



@router.get('/{id}',status_code=status.HTTP_202_ACCEPTED)
def get_admin(id: int, db: Session = Depends(get_db_read)):
    with db as session:
        try:
            # Try to retrieve the data from Redis cache
            cache_key = f'padmin:{id}'
            cached_admin = redis_client.get(cache_key)
            if cached_admin:
                return json.loads(cached_admin)

            # If not in cache, query the database
            admin = session.query(models.ProjectAdmin).filter(models.ProjectAdmin.id == id).first()

            if admin:
                # Convert the project object to a dictionary
                admin_data = admin.to_dict()

                # Cache the data in Redis with the specified TTL
                redis_client.setex(cache_key, cache_ttl, json.dumps(admin_data))

                return admin_data
            else:
                raise HTTPException(status_code=404, detail="Admin not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)
        



@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED)
def update_admin(id: int, updated_admin: schemas.UploadAdmin, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            admin_query = session.query(models.ProjectAdmin).filter(models.ProjectAdmin.id == id)
            admin = admin_query.first()

            if admin:
                # Update non-relationship attributes
                admin_data = updated_admin.dict(exclude={"experiences","educations"})
                admin_query.update(admin_data, synchronize_session=False)

                # Clear existing relationships (experiences) and update with new ones
                admin.experiences = []
                admin.educations = []

                for education_date in updated_admin.educations:
                    new_education = models.Education(**education_date.dict())
                    admin.educations.append(new_education)

                for experience_data in updated_admin.experiences:
                    new_experience = models.Experience(**experience_data.dict())
                    admin.experiences.append(new_experience)

                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                # Refresh the admin object to ensure it reflects the updated state
                session.refresh(admin)

                return admin.to_dict()  # Return the updated admin object as a dictionary

            else:
                raise HTTPException(status_code=404, detail="Admin not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)




@router.delete('/{id}', status_code=status.HTTP_202_ACCEPTED)
def delete_admin(id: int, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            # Retrieve the admin record to be deleted
            admin_to_delete = session.query(models.ProjectAdmin).get(id)

            if admin_to_delete:
                # Clear relationships
                admin_to_delete.experiences = []

                # Delete the admin record
                session.delete(admin_to_delete)
                session.commit()

            else:
                raise HTTPException(status_code=404, detail="Admin not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)