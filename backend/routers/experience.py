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
    prefix='/experience',
    tags=['Experience']
)

redis_client = redis.Redis(host='13.48.5.200', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds



@router.get('',status_code=status.HTTP_202_ACCEPTED)
def experience(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_exp = redis_client.get("experience")
    if cached_exp:
        # If found in the cache, decode the JSON and return the cached data
        exp_dict = json.loads(cached_exp)

        # Check if products are still in the database
        with db as session:
            exp_in_db = session.query(models.Experience).all()

        if not exp_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("experience")

            return []
    else:
        with db as session:
            try:
                exps = session.query(models.Experience).all()
                exp_dict = [exp.to_dict() for exp in exps]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("experience", cache_ttl, json.dumps(exp_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return exp_dict



@router.post('/{contributor_id}',status_code=status.HTTP_201_CREATED)
def upload_experience(contributor_id: int,experience_data: schemas.UploadExp, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            new_experience = models.Experience(**experience_data.dict())
            contributor.experiences.append(new_experience)
            session.commit()
            session.refresh(new_experience)

            # Clear the "products" cache after a new product is added
            redis_client.flushall()

            return new_experience
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
            


@router.put('/{contributor_id}/{experience_id}', status_code=status.HTTP_200_OK)
def update_experience(contributor_id: int, experience_id: int, experience_data: schemas.UploadExp, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Retrieve the contributor and the experience
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            experience = session.query(models.Experience).filter(models.Experience.id == experience_id).first()
            if not experience:
                raise HTTPException(status_code=404, detail="Experience not found")

            # Update the experience data
            for key, value in experience_data.dict().items():
                setattr(experience, key, value)

            session.commit()

            # Clear all data stored in Redis
            redis_client.flushall()

            return experience
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")



@router.delete('/{contributor_id}/{experience_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(contributor_id: int, experience_id: int, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            # Retrieve the contributor and the experience
            contributor = session.query(models.Contributor).filter(models.Contributor.id == contributor_id).first()
            if not contributor:
                raise HTTPException(status_code=404, detail="Contributor not found")
            
            experience = session.query(models.Experience).filter(models.Experience.id == experience_id).first()
            if not experience:
                raise HTTPException(status_code=404, detail="Experience not found")

            # Remove the experience from the contributor's experiences
            contributor.experiences.remove(experience)
            session.commit()

            # Delete the experience
            session.delete(experience)
            session.commit()

            # Clear all data stored in Redis
            redis_client.flushall()

            # Return successful deletion response
            return None
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")