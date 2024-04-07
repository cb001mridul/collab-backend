from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from sqlalchemy import func
from typing import List,Optional
from .. import models,schemas
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix='/education',
    tags=['Education']
)

redis_client = redis.Redis(host='13.48.5.200', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds



@router.get('',status_code=status.HTTP_202_ACCEPTED)
def education(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_edu = redis_client.get("education")
    if cached_edu:
        # If found in the cache, decode the JSON and return the cached data
        edu_dict = json.loads(cached_edu)

        # Check if products are still in the database
        with db as session:
            edu_in_db = session.query(models.Education).all()

        if not edu_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("education")

            return []
    else:
        with db as session:
            try:
                edus = session.query(models.Education).all()
                edu_dict = [edu.to_dict() for edu in edus]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("education", cache_ttl, json.dumps(edu_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return edu_dict



@router.post('/{contributor_id}',status_code=status.HTTP_201_CREATED)
def upload_education(contributor_id: int,education_data: schemas.UploadEdu, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            new_education = models.Education(**education_data.dict())
            contributor.educations.append(new_education)
            session.commit()
            session.refresh(new_education)

            # Clear the "products" cache after a new product is added
            redis_client.flushall()

            return new_education
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
            


@router.put('/{contributor_id}/{education_id}', status_code=status.HTTP_200_OK)
def update_education(contributor_id: int, education_id: int, education_data: schemas.UploadEdu, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Retrieve the contributor and the experience
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            education = session.query(models.Education).filter(models.Education.id == education_id).first()
            if not education:
                raise HTTPException(status_code=404, detail="Education not found")

            # Update the experience data
            for key, value in education_data.dict().items():
                setattr(education, key, value)

            session.commit()

            # Clear all data stored in Redis
            redis_client.flushall()

            return education
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")



@router.delete('/{contributor_id}/{education_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_education(contributor_id: int, education_id: int, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Retrieve the contributor and the experience
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            education = session.query(models.Education).filter(models.Education.id == education_id).first()
            if not education:
                raise HTTPException(status_code=404, detail="Education not found")

            # Remove the experience from the contributor's experiences
            contributor.educations.remove(education)
            session.commit()

            # Delete the experience
            session.delete(education)
            session.commit()

            # Clear all data stored in Redis
            redis_client.flushall()

            # Return successful deletion response
            return None
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")