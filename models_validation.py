import enum
from pydantic.dataclasses import dataclass
from pydantic import Field, StrictFloat, StrictInt, StrictStr, PositiveInt


# --------------------------------------------------->         USER
@dataclass(slots=True)
class User:
    name: StrictStr
    username: StrictStr
    email: StrictStr
    pwd: StrictStr
    cpwd: StrictStr
    # admin: StrictBool


@dataclass(slots=True)
class UserLogin:
    emailname: StrictStr = Field(description="Username/Email")
    pwd: StrictStr = Field()
    cpwd: StrictStr = Field()


# --------------------------------------------------->         COURSE


class course_type(enum.Enum):
    UG = "UG"
    PG = "PG"
    Integrated = "Integrated"


@dataclass(slots=True)
class Course:
    name: StrictStr
    duration: PositiveInt
    type: course_type
    elig: StrictStr


# --------------------------------------------------->         COLLEGE
@dataclass(slots=True)
class College:
    name: StrictStr
    rank: PositiveInt
    email: StrictStr
    city: StrictStr
    state: StrictStr
    country: StrictStr
    address: StrictStr


# --------------------------------------------------->         EXAM
@dataclass(slots=True)
class Exam:
    name: StrictStr
    elig: StrictStr
    syllabus: StrictStr
    fee: StrictFloat


# --------------------------------------------------->         ACADEMICS
@dataclass(slots=True)
class Academics:
    course_id: StrictInt
    college_id: StrictInt
    exam_id: StrictInt
    course_fee: StrictFloat
    cutoff_rank: StrictInt


# --------------------------------------------------->         POST
@dataclass(slots=True)
class Post:
    title: StrictStr
    body: StrictStr


class view(enum.Enum):
    Private = "Private"
    Public = "Public"


# --------------------------------------------------->         LIST
@dataclass(slots=True)
class List:
    course_id: StrictInt
    view: view
