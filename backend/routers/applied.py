from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from .. import models,schemas,auth2
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError

redis_client = redis.Redis(host='51.20.142.197', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds

router = APIRouter(
    prefix='/applied',
    tags=['Applied']
)


@router.get('',status_code=status.HTTP_202_ACCEPTED)
def applied(
    db: Session = Depends(get_db_read),
    ):
    cached_applied = redis_client.get("applied")
    if cached_applied:
        applied_dict = json.loads(cached_applied)
        with db as session:
            applied_in_db = session.query(models.Applied).all()

        if not applied_in_db:
            redis_client.delete("applied")

            return []
    else:
        with db as session:
            try:
                applies = session.query(models.Applied).all()
                applied_dict = [applied.to_dict() for applied in applies]

                redis_client.setex("applied", cache_ttl, json.dumps(applied_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return applied_dict



@router.post('',status_code=status.HTTP_201_CREATED)
def upload_apply(request: schemas.Apply, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            new_apply = models.Applied(**request.dict())
            session.add(new_apply)
            session.commit()
            session.refresh(new_apply)

            redis_client.delete("applied")

            return new_apply
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.get('/{id}',status_code=status.HTTP_202_ACCEPTED)
def get_apply(id: int, db: Session = Depends(get_db_read)):
    with db as session:
        try:
            # Try to retrieve the data from Redis cache
            cache_key = f'applied:{id}'
            cached_applied = redis_client.get(cache_key)
            if cached_applied:
                return json.loads(cached_applied)

            # If not in cache, query the database
            applied = session.query(models.Applied).filter(models.Applied.id == id).first()

            if applied:
                # Convert the project object to a dictionary
                applied_data = applied.to_dict()

                # Cache the data in Redis with the specified TTL
                redis_client.setex(cache_key, cache_ttl, json.dumps(applied_data))

                return applied_data
            else:
                raise HTTPException(status_code=404, detail="Applied details not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.put('/{id}',status_code=status.HTTP_200_OK)
def update_apply(id: int, applied_project: schemas.Apply, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            apply_query = session.query(models.Applied).filter(models.Applied.id == id)
            apply = apply_query.first()

            if apply:
                # Update the product in the database
                apply_query.update(applied_project.dict(), synchronize_session=False)
                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                return apply_query.first()

            else:
                raise HTTPException(status_code=404, detail="Applied details not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.delete('/{id}',status_code=status.HTTP_200_OK)
def delete_apply(id: int,db: Session = Depends(get_db_write)):

    with db as session:
        try:
            delete_apply = session.query(models.Applied).filter(models.Applied.id == id)
            delete_apply.delete(synchronize_session=False)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")