from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


class MixIdUrl:
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)


tag_post = Table(
    'tag_post',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Post(Base, MixIdUrl):
    __tablename__ = 'post'
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship('Author')
    tags = relationship('Tag', secondary=tag_post)
    image_id = Column(Integer, ForeignKey('images.id'))
    image = relationship('Images')
    date = Column(DateTime)
    comments = relationship('Comments')


class Author(Base, MixIdUrl):
    __tablename__ = 'author'
    name = Column(String, nullable=False)
    posts = relationship('Post')


class Tag(Base, MixIdUrl):
    __tablename__ = 'tag'
    name = Column(String, nullable=False)
    posts = relationship('Post', secondary=tag_post)


class Images(Base, MixIdUrl):
    __tablename__ = 'images'


class Comments(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    author_name = Column(String, nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'))
    post = relationship('Post')
    url = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.comment_id'))
    parent = relationship('Comments')