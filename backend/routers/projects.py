from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
from ..database import get_db_read,get_db_write
from sqlalchemy import func
from typing import List,Optional
from .. import models,schemas,auth2
from sqlalchemy.orm import Session
import redis
import json
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix='/projects',
    tags=['Projects']
)

redis_client = redis.Redis(host='13.53.182.223', port=6379, db=0)
cache_ttl = 60  # Cache time-to-live in seconds


@router.get('',status_code=status.HTTP_202_ACCEPTED)
def projects(db: Session = Depends(get_db_read)):

    # Check if products are available in the Redis cache
    cached_projects = redis_client.get("projects")
    if cached_projects:
        # If found in the cache, decode the JSON and return the cached data
        projects_dict = json.loads(cached_projects)

        # Check if products are still in the database
        with db as session:
            projects_in_db = session.query(models.Project).all()

        if not projects_in_db:
            # Products have been deleted from the database, so delete the cached data
            redis_client.delete("projects")

            return []
    else:
        with db as session:
            try:
                projects = session.query(models.Project).all()
                projects_dict = [project.to_dict() for project in projects]

                # Cache the result in Redis after JSON serialization
                redis_client.setex("projects", cache_ttl, json.dumps(projects_dict))
            except SQLAlchemyError as e:
                session.rollback()
                raise HTTPException(status_code=500, detail="Database error")

    return projects_dict



@router.post('',status_code=status.HTTP_201_CREATED)
def upload_project(request: schemas.ProjectUpload, db: Session = Depends(get_db_write)):
    with db as session:
        try:
            new_project = models.Project(**request.dict())
            session.add(new_project)
            session.commit()
            session.refresh(new_project)

            # Clear the "products" cache after a new product is added
            redis_client.delete("projects")

            return new_project
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.get('/{id}',status_code=status.HTTP_202_ACCEPTED)
def get_project(id: int, db: Session = Depends(get_db_read)):
    with db as session:
        try:
            # Try to retrieve the data from Redis cache
            cache_key = f'projects:{id}'
            cached_project = redis_client.get(cache_key)
            if cached_project:
                return json.loads(cached_project)

            # If not in cache, query the database
            project = session.query(models.Project).filter(models.Project.id == id).first()

            if project:
                # Convert the project object to a dictionary
                project_data = project.to_dict()

                # Cache the data in Redis with the specified TTL
                redis_client.setex(cache_key, cache_ttl, json.dumps(project_data))

                return project_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")




@router.put('/{id}',status_code=status.HTTP_200_OK)
def update_project(id: int, updated_project: schemas.ProjectUpload, db: Session = Depends(get_db_write)):

    with db as session:
        try:
            project_query = session.query(models.Project).filter(models.Project.id == id)
            project = project_query.first()

            if project:
                # Update the product in the database
                project_query.update(updated_project.dict(), synchronize_session=False)
                session.commit()

                # Clear the entire data inside Redis (flush the current database)
                redis_client.flushdb()

                return project_query.first()

            else:
                raise HTTPException(status_code=404, detail="Project not found")

        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")
        


@router.delete('/{id}',status_code=status.HTTP_200_OK)
def delete_project(id: int,db: Session = Depends(get_db_write)):

    with db as session:
        try:
            delete_project = session.query(models.Project).filter(models.Project.id == id)
            delete_project.delete(synchronize_session=False)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail="Database error")