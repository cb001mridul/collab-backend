# from fastapi import FastAPI,Response,status,HTTPException,Depends,APIRouter
# from ..database import get_db_read,get_db_write
# from sqlalchemy import func
# from typing import List,Optional
# from .. import models,schemas
# from sqlalchemy.orm import Session
# import redis
# import json
# from sqlalchemy.exc import SQLAlchemyError

# router = APIRouter(
#     prefix='/experience',
#     tags=['Experience']
# )

# redis_client = redis.Redis(host='localhost', port=6379, db=0)
# cache_ttl = 60  # Cache time-to-live in seconds



# @router.get('',status_code=status.HTTP_202_ACCEPTED)
# def experience(db: Session = Depends(get_db_read)):

#     # Check if products are available in the Redis cache
#     cached_exp = redis_client.get("experience")
#     if cached_exp:
#         # If found in the cache, decode the JSON and return the cached data
#         exp_dict = json.loads(cached_exp)

#         # Check if products are still in the database
#         with db as session:
#             exp_in_db = session.query(models.Experience).all()

#         if not exp_in_db:
#             # Products have been deleted from the database, so delete the cached data
#             redis_client.delete("experience")

#             return []
#     else:
#         with db as session:
#             try:
#                 exps = session.query(models.Experience).all()
#                 exp_dict = [exp.to_dict() for exp in exps]

#                 # Cache the result in Redis after JSON serialization
#                 redis_client.setex("experience", cache_ttl, json.dumps(exp_dict))
#             except SQLAlchemyError as e:
#                 session.rollback()
#                 raise HTTPException(status_code=500, detail="Database error")

#     return exp_dict