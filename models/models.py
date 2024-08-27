
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, TIMESTAMP, Date, ForeignKey, Float, MetaData, Enum
from datetime import datetime
import enum
from sqlalchemy import Table, Column, Integer, String, Float, Text, Boolean, ForeignKey, Enum, MetaData
import enum

metadata = MetaData()

class WorkModeEnum(enum.Enum):
    online = "online"
    offline = "offline"


class JobTypeEnum(enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    one_time_project = "one_time_project"  
    internship = "internship"




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
    Column('is_superuser', Boolean, default=False),
    Column('telegram_username', String), 
    Column('phone_number', String) 
)

seller = Table(
    'seller',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('user.id',ondelete='CASCADE')),
    Column('image_url', Text),
    Column('description', Text),
    Column('cv_url', Text),
    Column('birth_date', Date)
)


occupation = Table(
    'occupation',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('occup_name', String, nullable=False)
)


seller_occupation = Table(
    'seller_occupation',
    metadata,
    Column('seller_id', Integer, ForeignKey('seller.id', ondelete='CASCADE'), primary_key=True),
    Column('occupation_id', Integer, ForeignKey('occupation.id', ondelete='CASCADE'), primary_key=True)
)


skills = Table(
    'skills',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('skill_name', String, nullable=False)
)


seller_skills = Table(
    'seller_skills',
    metadata,
    Column('seller_id', Integer, ForeignKey('seller.id', ondelete='CASCADE'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
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
    Column('status', Boolean, default=True, nullable=False),
    Column('category_id', Integer, ForeignKey('gigs_category.id', ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('user.id', ondelete='CASCADE')),
    Column('job_type', Enum(JobTypeEnum), nullable=False),  
     Column('work_mode', Enum(WorkModeEnum), nullable=False)
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
    Column('price', Float, nullable=False),
    Column('delivery_days', Integer),
    Column('seller_id', Integer, ForeignKey('seller.id',ondelete='CASCADE')),
    Column('description', Text),
    Column('status', Boolean,default=True,nullable=False)
)





experience = Table(
    'experience',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('company_name', String, nullable=False),
    Column('start_date', Date),
    Column('end_date', Date),
    Column('seller_id', Integer, ForeignKey('seller.id',ondelete='CASCADE')),
    Column('city', String),
    Column('country', String),
    Column('job_title', String),
    Column('description', Text)
)



certificate = Table(
    'certificate',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('pdf_url', Text),
    Column('seller_id', Integer, ForeignKey('seller.id',ondelete='CASCADE'))
)



project_files = Table(
    'project_files',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file_url', Text),
    Column('seller_project_id', Integer, ForeignKey('seller_projects.id',ondelete='CASCADE'))
)



saved_client = Table(
    'saved_client',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('seller_id', Integer, ForeignKey('seller.id',ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('user.id',ondelete='CASCADE'))
)

saved_seller = Table(
    'saved_seller',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('user.id',ondelete='CASCADE')),
    Column('seller_id', Integer, ForeignKey('seller.id',ondelete='CASCADE'))
)



