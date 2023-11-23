from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from sqlalchemy import func
from typing import List,Optional
from .. import models,schemas
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError
import traceback

router = APIRouter(
    prefix='/contributor',
    tags=['Contributor']
)

redis_client = redis.Redis(host='13.48.48.177', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds


@router.get('',status_code=status.HTTP_202_ACCEPTED)
def contributors(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_contrib = redis_client.get("contributors")
    if cached_contrib:
        # If found in the cache, decode the JSON and return the cached data
        contrib_dict = json.loads(cached_contrib)

        # Check if products are still in the database
        with db as session:
            contribs_in_db = session.query(models.Contributor).all()

        if not contribs_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("contributors")

            return []
    else:
        with db as session:
            try:
                contribs = session.query(models.Contributor).all()
                contrib_dict = [contrib.to_dict() for contrib in contribs]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("contributors", cache_ttl, json.dumps(contrib_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return contrib_dict



@router.post('', status_code=status.HTTP_201_CREATED)
def upload_contributor(request: schemas.UploadContributor, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Convert Pydantic model to dictionary for ProjectAdmin creation
            contrib_data = request.dict()

            # Extract educations and experiences from request
            educations_data = contrib_data.pop("educations", [])
            experiences_data = contrib_data.pop("experiences", [])

            # Create a new ProjectAdmin instance
            new_contrib = models.Contributor(**contrib_data)

            # Add experiences and educations
            for experience_data in experiences_data:
                new_experience = models.Experience(**experience_data)  # Use the dictionary as it is
                new_contrib.experiences.append(new_experience)
            
            for education_data in educations_data:
                new_education = models.Education(**education_data)  # Use the dictionary as it is
                new_contrib.educations.append(new_education)

            # Add the new admin to the session
            session.add(new_contrib)
            session.commit()
            session.refresh(new_contrib)

            # Clear the cache
            redis_client.delete("contributors")

            return request

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)
        


@router.get('/{id}',status_code=status.HTTP_202_ACCEPTED)
def get_contrib(id: int, db: Session = Depends(get_db_read)):
    with db as session:
        try:
            # Try to retrieve the data from Redis cache
            cache_key = f'contributors:{id}'
            cached_contrib = redis_client.get(cache_key)
            if cached_contrib:
                return json.loads(cached_contrib)

            # If not in cache, query the database
            contrib = session.query(models.Contributor).filter(models.Contributor.id == id).first()

            if contrib:
                # Convert the project object to a dictionary
                contrib_data = contrib.to_dict()

                # Cache the data in Redis with the specified TTL
                redis_client.setex(cache_key, cache_ttl, json.dumps(contrib_data))

                return contrib_data
            else:
                raise HTTPException(status_code=404, detail="Contributor not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)
        


@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED)
def update_contributor(id: int, updated_contrib: schemas.UploadContributor, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            contrib_query = session.query(models.Contributor).filter(models.Contributor.id == id)
            contrib = contrib_query.first()

            if contrib:
                # Update non-relationship attributes
                contrib_data = updated_contrib.dict(exclude={"experiences","educations"})
                contrib_query.update(contrib_data, synchronize_session=False)

                # Clear existing relationships (experiences) and update with new ones
                contrib.experiences = []
                contrib.educations = []

                for education_date in updated_contrib.educations:
                    new_education = models.Education(**education_date.dict())
                    contrib.educations.append(new_education)

                for experience_data in updated_contrib.experiences:
                    new_experience = models.Experience(**experience_data.dict())
                    contrib.experiences.append(new_experience)

                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                # Refresh the admin object to ensure it reflects the updated state
                session.refresh(contrib)

                return contrib.to_dict()  # Return the updated admin object as a dictionary

            else:
                raise HTTPException(status_code=404, detail="Contributor not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)
        


@router.put('/{id}',status_code=status.HTTP_202_ACCEPTED)
def update_contrib(id: int, updated_contrib: schemas.UploadContributor, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            contrib_query = session.query(models.Contributor).filter(models.Contributor.id == id)
            contrib = contrib_query.first()

            if contrib:
                # Update the product in the database
                contrib_query.update(updated_contrib.dict(), synchronize_session=False)
                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                return contrib_query.first()

            else:
                raise HTTPException(status_code=404, detail="Contributor not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.delete('/{id}', status_code=status.HTTP_202_ACCEPTED)
def delete_admin(id: int, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            # Retrieve the admin record to be deleted
            contrib_to_delete = session.query(models.Contributor).get(id)

            if contrib_to_delete:
                # Clear relationships
                contrib_to_delete.experiences = []

                # Delete the admin record
                session.delete(contrib_to_delete)
                session.commit()

            else:
                raise HTTPException(status_code=404, detail="Contributor not found")

        except SQLAlchemyError as e:
            session.rollback()
            error_message = f"Database error: {str(e)}"
            traceback.print_exc()  # Print the traceback for debugging purposes
            raise HTTPException(status_code=500, detail=error_message)