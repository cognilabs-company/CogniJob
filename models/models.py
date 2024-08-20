
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, TIMESTAMP, Date, ForeignKey, Float, MetaData, Enum
from datetime import datetime
import enum

metadata = MetaData()


user = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('first_name', String),
    Column('last_name', String),
    Column('email', String, nullable=False),
    Column('username', String, nullable=False, unique=True),
    Column('password', String, nullable=False),
    Column('registered_date', TIMESTAMP, default=datetime.utcnow),
    Column('is_seller', Boolean, default=False),
    Column('is_client', Boolean, default=False),
    Column('is_superuser', Boolean, default=False)
)

seller = Table(
    'seller',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('image_url', Text),
    Column('description', Text),
    Column('cv_url', Text),
    Column('birth_date', Date)
)

skills = Table(
    'skills',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('skill_name', String, nullable=False),
    Column('seller_id', Integer, ForeignKey('seller.id'))
)


gigs_category = Table(
    'gigs_category',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('category_name', String, nullable=False)

)

gigs = Table(
    'gigs',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('gigs_title', String, nullable=False),
    Column('duration', Integer),
    Column('price', Float, nullable=False),
    Column('description', Text),
    Column('status',Boolean,default=True,nullable=False),
    Column('category_id',Integer,ForeignKey('gigs_category.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)



gigs_tags = Table(
    'gigs_tags',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tag_name', String, nullable=False)
   
)


gig_tag_association = Table(
    'gig_tag_connect',
    metadata,
    Column('gig_id', Integer, ForeignKey('gigs.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('gigs_tags.id', ondelete='CASCADE'), primary_key=True)
)






gigs_file = Table(
    'gigs_file',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file_url', Text),
    Column('gigs_id', Integer, ForeignKey('gigs.id',ondelete='CASCADE'))
)


seller_projects = Table(
    'seller_projects',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('title', String, nullable=False),
    Column('category', String, ),
    Column('price', Float, nullable=False),
    Column('delivery_days', Integer),
    Column('seller_id', Integer, ForeignKey('seller.id')),
    Column('description', Text),
    Column('status', String)
)


# client = Table(
#     'client',
#     metadata,
#     Column('id', Integer, primary_key=True, autoincrement=True),
#     Column('user_id', Integer, ForeignKey('user.id'))
# )

language = Table(
    'language',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('lan_name', String, nullable=False),
    Column('seller_id', Integer, ForeignKey('seller.id'))
)

experience = Table(
    'experience',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('company_name', String, nullable=False),
    Column('start_date', Date),
    Column('end_date', Date),
    Column('seller_id', Integer, ForeignKey('seller.id')),
    Column('city', String),
    Column('country', String),
    Column('job_title', String),
    Column('description', Text)
)

projects_skills = Table(
    'projects_skills',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('skill_name', String, nullable=False),
    Column('seller_project_id', Integer, ForeignKey('seller_projects.id'))
)

certificate = Table(
    'certificate',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('pdf_url', Text),
    Column('seller_id', Integer, ForeignKey('seller.id'))
)



occupation = Table(
    'occupation',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('occup_name', String, nullable=False),
    Column('seller_id', Integer, ForeignKey('seller.id'))
)

project_files = Table(
    'project_files',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file_url', Text),
    Column('seller_project_id', Integer, ForeignKey('seller_projects.id'))
)



saved_client = Table(
    'saved_client',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('seller_id', Integer, ForeignKey('seller.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)

saved_seller = Table(
    'saved_seller',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('seller_id', Integer, ForeignKey('seller.id'))
)
