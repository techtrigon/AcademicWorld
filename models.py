from typing import Any
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    DeclarativeBase,
    MappedAsDataclass,
)
from sqlalchemy.orm.relationships import Relationship
# from sqlalchemy.orm.properties import MappedColumn


class Base(DeclarativeBase, MappedAsDataclass): ...


class User(Base):
    __tablename__ = "User"
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    pwd: Mapped[str]
    username: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[Any] = mapped_column(DateTime, server_default=func.now())
    admin: Mapped[bool] = mapped_column(default=False)

    # def __repr__(self) -> str:
    #     return f"<User:{self.username}>"


class Course(Base):
    __tablename__ = "Course"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    duration: Mapped[int]
    type: Mapped[str]
    elig: Mapped[str]
    likes: Mapped[int] = mapped_column(default=0)

    # def __repr__(self) -> str:
    #     return f"<Course:{self.id}-{self.name}>"


class College(Base):
    __tablename__ = "College"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    rank: Mapped[int] = mapped_column(unique=True, nullable=True)
    city: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=True)
    state: Mapped[str] = mapped_column(nullable=True)
    country: Mapped[str] = mapped_column(nullable=True)
    address: Mapped[str]
    likes: Mapped[int] = mapped_column(default=0)

    # def __repr__(self) -> str:
    #     return f"<College:{self.id}-{self.name}>"


class Exam(Base):
    __tablename__ = "Exam"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)
    elig: Mapped[str]
    syllabus: Mapped[str]
    fee: Mapped[float]
    likes: Mapped[int] = mapped_column(default=0)
    # academics = relationship(
    #     "Academics",
    #     back_populates="exam",
    #     lazy="selectin",
    #     cascade="all, delete-orphan",
    # )

    # def __repr__(self) -> str:
    #     return f"<Exam:{self.id}-{self.name}>"


class Academics(Base):
    __tablename__ = "Academics"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # course: Relationship[Any] = relationship("Course", lazy="selectin")
    # college: Relationship[Any] = relationship("College", lazy="selectin")
    # exam: Relationship[Any] = relationship("Exam", lazy="selectin")
    course_id: Mapped[Any] = mapped_column(
        ForeignKey("Course.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
    )
    college_id: Mapped[Any] = mapped_column(
        ForeignKey("College.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    exam_id: Mapped[Any] = mapped_column(
        ForeignKey("Exam.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    course_fee: Mapped[float]
    cutoff_rank: Mapped[int]
    __table_args__ = (
        UniqueConstraint("course_id", "college_id", "exam_id", name="CHECKKEY"),
    )


# ----------------------------------------------------->    POST & REPLY


class Post(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column()
    body: Mapped[str] = mapped_column()
    user_id: Mapped[Any] = mapped_column(
        ForeignKey("User.username", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[Any] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


# .......................... COURSE POST & REPLIES


class CoursePost(Post):
    __tablename__ = "CoursePost"
    course_id: Mapped[Any] = mapped_column(
        ForeignKey("Course.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    coursepost_id: Mapped[Any] = mapped_column(
        ForeignKey("CoursePost.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )


# .......................... COLLEGE POST & REPLIES


class CollegePost(Post):
    __tablename__ = "CollegePost"
    college_id: Mapped[Any] = mapped_column(
        ForeignKey("College.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    collegepost_id: Mapped[Any] = mapped_column(
        ForeignKey("CollegePost.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )


# .......................... EXAM POST & REPLIES


class ExamPost(Post):
    __tablename__ = "ExamPost"
    exam_id: Mapped[Any] = mapped_column(
        ForeignKey("Exam.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    exampost_id: Mapped[Any] = mapped_column(
        ForeignKey("ExamPost.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True
    )


# ----------------------------------------------------->    LIST & LIKES


# .......................... LIST
class List(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Any] = mapped_column(
        ForeignKey("User.username", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    view: Mapped[str] = mapped_column(default="Private")


class CourseList(List):
    __tablename__ = "CourseList"
    course_id = mapped_column(
        ForeignKey("Course.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )  # type: ignore
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)


class CollegeList(List):
    __tablename__ = "CollegeList"
    college_id = mapped_column(
        ForeignKey("College.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )  # type: ignore
    __table_args__ = (UniqueConstraint("college_id", "user_id"),)


class ExamList(List):
    __tablename__ = "ExamList"
    exam_id = mapped_column(
        ForeignKey("Exam.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )  # type: ignore
    __table_args__ = (UniqueConstraint("exam_id", "user_id"),)


# .......................... LIKES
class Likes(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Any] = mapped_column(
        ForeignKey("User.username", ondelete="CASCADE", onupdate="CASCADE"),
    )


class CourseLikes(Likes):
    __tablename__ = "CourseLikes"
    course_id: Mapped[Any] = mapped_column(
        ForeignKey("Course.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)


class CollegeLikes(Likes):
    __tablename__ = "CollegeLikes"
    college_id: Mapped[Any] = mapped_column(
        ForeignKey("College.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("college_id", "user_id"),)


class ExamLikes(Likes):
    __tablename__ = "ExamLikes"
    exam_id: Mapped[Any] = mapped_column(
        ForeignKey("Exam.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("exam_id", "user_id"),)
