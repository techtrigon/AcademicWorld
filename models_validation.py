import enum
from dataclasses import dataclass


# --------------------------------------------------->         USER
@dataclass(slots=True)
class User:
    name: str
    username: str
    email: str
    pwd: str
    cpwd: str

    def __post_init__(self):
        self.name = self.name.title()


@dataclass(slots=True)
class UserLogin:
    emailname: str
    pwd: str
    cpwd: str


# --------------------------------------------------->         COURSE


class course_type(enum.Enum):
    UG = "UG"
    PG = "PG"
    Integrated = "Integrated"


@dataclass(slots=True)
class Course:
    name: str
    duration: int
    type: course_type
    elig: str


# --------------------------------------------------->         COLLEGE
@dataclass(slots=True)
class College:
    name: str
    rank: int
    email: str
    city: str
    state: str
    country: str
    address: str

    def __post_init__(self):
        self.name = self.name.title()


# --------------------------------------------------->         EXAM
@dataclass(slots=True)
class Exam:
    name: str
    elig: str
    syllabus: str
    fee: float


# --------------------------------------------------->         ACADEMICS
@dataclass(slots=True)
class Academics:
    course_id: int
    college_id: int
    exam_id: int
    course_fee: float
    cutoff_rank: int


# --------------------------------------------------->         POST
@dataclass(slots=True)
class Post:
    title: str
    body: str


class view(enum.Enum):
    Private = "Private"
    Public = "Public"


# --------------------------------------------------->         LIST
@dataclass(slots=True)
class List:
    course_id: int
    view: view
