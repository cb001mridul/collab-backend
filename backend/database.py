# database.py

import logging
import threading
import asyncio
import concurrent.futures
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

####################### LOGGING ##########################

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

######################  LOGGING ############################

# Increase the number of ThreadPoolExecutor workers to handle multithreading within each process
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=15)

######################### CONFIGURATIONS ########################

SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:zasx@13.48.5.200:5432/collab"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=40,      # The initial size of the connection pool
    max_overflow=50,   # The maximum number of connections that can be created beyond the pool_size
)

# SessionLocal for reading (autocommit=True for read-only operations)
SessionLocalRead = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# SessionLocal for writing (autocommit=False for write operations)
SessionLocalWrite = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
thread_local = threading.local()

Base = declarative_base()

######################### CONFIGURATIONS ########################

############# MULTITHREADING ##############################

async def get_db_read():
    # If the current thread already has a read session, return it
    if hasattr(thread_local, "session_read"):
        return thread_local.session_read

    # If not, create a new read session for the current thread
    loop = asyncio.get_event_loop()

    # Log when a new read database session is created for a thread
    pool = engine.pool
    pool_info = f"Pool Size: {pool.size()}, Checked out: {pool.checkedout()}, Overflow: {pool.overflow()}"

    # Request a read database session from the thread pool using the event loop
    db_read = await loop.run_in_executor(thread_pool, SessionLocalRead)

    # Store the read session in thread-local storage
    thread_local.session_read = db_read

    return db_read

############# MULTITHREADING ##############################

############# MULTIPROCESSING ##############################

# Use a separate ProcessPoolExecutor for multiprocessing

# thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=15)

async def get_db_write():
    # If the current thread already has a write session, return it
    if hasattr(thread_local, "session_write"):
        return thread_local.session_write

    # If not, create a new write session for the current thread
    loop = asyncio.get_event_loop()

    # Log when a new write database session is created for a thread
    pool = engine.pool
    pool_info = f"Pool Size: {pool.size()}, Checked out: {pool.checkedout()}, Overflow: {pool.overflow()}"

    # Request a write database session from the thread pool using the event loop
    db_write = await loop.run_in_executor(thread_pool, SessionLocalWrite)

    # Store the write session in thread-local storage
    thread_local.session_write = db_write

    return db_write