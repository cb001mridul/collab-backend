from click import DateTime
from .database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float,ARRAY,Text,Date,func,Table
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.hybrid import hybrid_property



projectadmin_experience_association = Table(
    'projectadmin_experience_association',
    Base.metadata,
    Column('projectadmin_id', Integer, ForeignKey('padmin.id')),
    Column('experience_id', Integer, ForeignKey('experience.id'))
)

projectadmin_education_association = Table(
    'projectadmin_education_association',
    Base.metadata,
    Column('projectadmin_id', Integer, ForeignKey('padmin.id')),
    Column('education_id', Integer, ForeignKey('education.id'))
)


contributor_experience_association = Table(
    'contributor_experience_association',
    Base.metadata,
    Column('contributor_id', Integer, ForeignKey('contributors.id')),
    Column('experience_id', Integer, ForeignKey('experience.id'))
)


contributor_education_association = Table(
    'contributor_education_association',
    Base.metadata,
    Column('contributor_id', Integer, ForeignKey('contributors.id')),
    Column('education_id', Integer, ForeignKey('education.id'))
)



class User(Base):

    __tablename__ = "users"

    id = Column(Integer,nullable=False,primary_key=True)
    organisation = Column(String,nullable=False)
    email = Column(EmailType,nullable=False,unique=True)
    name = Column(String, nullable=False)
    password = Column(String,nullable=False)
    is_admin = Column(Boolean,default=False)
    is_contributor = Column(Boolean,default=False)
    verification_token = Column(String, unique=True, nullable=True)
    is_verified = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "is_admin": self.is_admin,
            "is_contributor": self.is_contributor
        }
    
    

class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, nullable=False, primary_key=True)
    company_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    start_date = Column(Date, default=func.current_date())
    end_date = Column(Date, default=func.current_date())

    projectadmins = relationship("ProjectAdmin", secondary=projectadmin_experience_association, overlaps="experiences")
    contributors = relationship("Contributor", secondary=contributor_experience_association, overlaps="experiences")

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.company_name,
            "position": self.position,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat()
        }
    


class Education(Base):

    __tablename__ = "education"

    id = Column(Integer,nullable=False,primary_key=True)
    institute = Column(String,nullable=False)
    degree = Column(String,nullable=False)
    start_date = Column(Date,default=func.current_date())
    end_date = Column(Date,default=func.current_date())

    projectadmins = relationship("ProjectAdmin", secondary=projectadmin_education_association, overlaps="educations")
    contributors = relationship("Contributor", secondary=contributor_education_association, overlaps="educations")

    def to_dict(self):
        return {
            "id": self.id,
            "institute": self.institute,
            "degree": self.degree,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat()
        }



class ProjectAdmin(Base):
    __tablename__ = "padmin"

    id = Column(Integer, nullable=False, primary_key=True)
    description = Column(String, nullable=False)
    profile_pic = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    is_active = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User")

    experiences = relationship("Experience", secondary=projectadmin_experience_association, overlaps="projectadmins")
    educations = relationship("Education",secondary=projectadmin_education_association,overlaps="projectadmins")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "profile_pic": self.profile_pic,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            # "is_admin": self.is_admin,
            "user_id": self.user_id,
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "is_admin": self.user.is_admin,
            },
            "experiences": [experience.to_dict() for experience in self.experiences],
            "educations": [education.to_dict() for education in self.educations]
        }



class Contributor(Base):

    __tablename__ = "contributors"

    id = Column(Integer,nullable=False,primary_key=True)
    name = Column(String,nullable=False)
    role = Column(String,nullable=False)
    stack = Column(ARRAY(String),nullable=False)
    bio = Column(Text,nullable=False)
    profile_pic = Column(String,nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))

    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    user = relationship("User")
    experiences = relationship("Experience", secondary=contributor_experience_association, overlaps="contributors")
    educations = relationship("Education", secondary=contributor_education_association, overlaps="contributors")

    def to_dict(self):

        return {

            "id": self.id,
            "name": self.name,
            "role": self.role,
            "stack": self.stack,
            "bio": self.bio,
            "profile_pic": self.profile_pic,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "is_contributor": self.user.is_contributor
            },
            "experiences": [experience.to_dict() for experience in self.experiences],
            "educations": [education.to_dict() for education in self.educations]
        }
    


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer,nullable=False,primary_key=True)
    title = Column(String,nullable=False)
    subtitle = Column(String,nullable=True)
    description = Column(Text,nullable=False)
    tech_used = Column(ARRAY(String),nullable=False)
    domain = Column(ARRAY(String),nullable=False)
    contributors_active = Column(Integer,default=0)
    contributors_needed = Column(Integer,default=0)
    date_started = Column(Date, default=func.current_date())
    user_id = Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    user = relationship("User")

    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "tech_used": self.tech_used,
            "domain": self.domain,
            "contributors_active": self.contributors_active,
            "contributors_needed": self.contributors_needed,
            "date_started": self.date_started.isoformat(),
            # "admin_id": self.admin_id,
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "is_admin": self.user.is_admin,
                "name": self.user.name
            }
        }


class Applied(Base):
    __tablename__ = "applied"

    id = Column(Integer, primary_key=True, nullable=False)
    contributor_id = Column(Integer, ForeignKey("contributors.id", ondelete="CASCADE"), nullable=False)
    
    # Define the relationship to Contributor
    contributor = relationship("Contributor")
    
    def to_dict(self):
        return {
            "id": self.id,
            "contributor": self.contributor.to_dict()  # Include contributor data in the dictionary
        }
# ifferent model for Exp and Education
# start date
# end date 
# institute