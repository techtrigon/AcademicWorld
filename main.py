from pydantic import validate_email
from pydantic_core import PydanticCustomError
from db_connenction import db_connection, provide_transaction
from sqlalchemy.ext.asyncio import AsyncSession
import models as md, models_validation as mv  # noqa: E401
from litestar import (
    Litestar,
    MediaType,
    Request,
    Response,
    patch,
    post,
    get,
    delete,
    Controller,
)
from typing import Annotated, Any, Optional, Sequence
from litestar.contrib.sqlalchemy.plugins import SQLAlchemySerializationPlugin
from sqlalchemy import desc, select, insert, update
from litestar.openapi import OpenAPIConfig
from litestar.params import Parameter, Body
from litestar.exceptions import (
    NotAuthorizedException,
    ValidationException,
    NotFoundException,
)
from litestar.handlers import BaseRouteHandler
from litestar.di import Provide
from sqlalchemy.exc import NoResultFound, IntegrityError
from litestar.config.response_cache import CACHE_FOREVER
from passlib.hash import pbkdf2_sha256 as securepwd
from jwt_authentication import jwt_cookie_auth
from litestar.connection import ASGIConnection


# -----------------------------------------------------------------------------> GUARD
# async def check_admin(request: Request, _: BaseRouteHandler) -> Any:
async def check_admin(connection: ASGIConnection, _: BaseRouteHandler) -> Any:
    print("CHECK  ADMIN ............................\n\n\n")
    # print(connection.user)
    if not connection.user.get("admin"):
        raise NotAuthorizedException("⚠️ NOT ALLOWED")


# ..........................................................................................     USER CONTROLLER 🔰


class usercontroller(Controller):
    path = "/user"
    tags = ["🟡   Users"]

    async def check_user(self, user_id: str, request: Request) -> str:
        # print("ENTERED")
        if request.user["user_id"] and not request.user.get("admin"):
            raise NotAuthorizedException("⚠️ NOT ALLOWED !!")
        return user_id

    dependencies = {"check_user_dep1": Provide(check_user, True)}

    @post("/login", media_type=MediaType.TEXT)
    async def login(
        self, request: Request, data: mv.UserLogin, db: AsyncSession
    ) -> Any:
        if data.pwd != data.cpwd:
            raise ValidationException("⚠️ Passwords don't match")
        userid = data.emailname

        stmt = select(md.User).where(
            (md.User.email == userid) | (md.User.username == userid)
        )
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO USER FOUND !!")
        if not securepwd.verify(data.pwd, res.pwd):
            raise ValidationException("⚠️ Incorrect Password !!")
        return jwt_cookie_auth.login(
            response_media_type=MediaType.TEXT,
            response_body="✅ LOGGED IN AS ADMIN"
            if res.admin
            else "✅ LOGGED IN AS NON-ADMIN",
            identifier=res.username,
            token_extras={"admin": res.admin},
        )

    @post("/logout", media_type=MediaType.TEXT)
    async def logout(self, request: Request) -> Any:
        # print(request.user)
        resp = Response("✅ LOGGED OUT")
        resp.delete_cookie("token")
        return resp

    @get("/", guards=[check_admin])
    async def users(self, request: Request, db: AsyncSession) -> list[md.User]:
        print("ENTERED ...........................\n")
        print(request.user)
        res = await db.scalars(select(md.User))
        return res._allrows()

    @post("/register", exclude_from_auth=True, media_type=MediaType.TEXT)
    async def register(self, data: mv.User, db: AsyncSession, request: Request) -> Any:
        try:
            validate_email(data.email)
        except PydanticCustomError:
            raise ValidationException("⚠️ Invalid Email")
        if data.pwd != data.cpwd:
            raise ValidationException("⚠️ Passwords don't match")
        stmt = insert(md.User).values(
            name=data.name,
            username=data.username,
            email=data.email,
            pwd=securepwd.hash(data.pwd),
        )
        try:
            await db.execute(stmt)
        except IntegrityError:
            return Response("⚠️ USER ALREADY EXISTS !!", status_code=400)
        return "✅ USER ADDED SUCCESSFULLY !!"

    @delete("/delete/{user_id:str}", status_code=200)
    async def user_delete(
        self,
        db: AsyncSession,
        check_user_dep1: Annotated[
            Any, Parameter(description="Username/Email to delete")
        ],
    ) -> str:
        user_id = check_user_dep1
        # print(user_id)
        stmt = select(md.User).where(
            (md.User.email == user_id) | (md.User.username == user_id)
        )
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO USER FOUND !!")
        await db.delete(res)
        return "✅ DELETED USER SUCCESSFULLY !!"


# ..........................................................................................     COURSE CONTROLLER 🔰

# ------------------------------------------------------------------->   COURSE 🟢


class coursecontroller(Controller):
    path = "/course"
    tags = ["🟢   Courses"]

    @get("/", exclude_from_auth=True)
    async def courses(self, db: AsyncSession) -> list[md.Course]:
        res = await db.scalars(select(md.Course))
        ans = res._allrows()
        return ans

    @post("/add", guards=[check_admin], media_type=MediaType.TEXT)
    async def course_add(self, data: mv.Course, db: AsyncSession) -> Any:
        try:
            data.duration = int(data.duration)
        except ValueError:
            raise ValidationException("⚠️ Duration can only be integer")
        if data.duration < 1:
            raise ValidationException("⚠️ Duration can't be less than than 1")
        stmt = insert(md.Course).values(
            name=data.name,
            duration=data.duration,
            type=data.type.value,
            elig=data.elig,
        )
        try:
            await db.execute(stmt)
        except Exception:
            return Response("⚠️ COURSE ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @patch("/update/{course_id:int}", guards=[check_admin], media_type=MediaType.TEXT)
    async def course_update(
        self,
        course_id: int,
        db: AsyncSession,
        data: dict = Body(
            title="Course",
            description='DEMO SCHEMA  =  { "name": " " , "duration": 0 , "type": " " , "elig": " " }',
        ),
    ) -> Any:
        stmt = update(md.Course).where(md.Course.id == course_id).values(**data)
        try:
            await db.execute(stmt)
        except Exception:
            return Response("⚠️ NO COURSE WITH THIS ID EXISTS !!", status_code=404)
        return "✅ UPDATED SUCCESSFULLY !!"

    @delete(
        "/delete/{course_id:int}",
        status_code=200,
        guards=[check_admin],
        media_type=MediaType.TEXT,
    )
    async def course_delete(
        self,
        course_id: Annotated[int, Parameter(description="ID of Course to delete")],
        db: AsyncSession,
    ) -> str | Response:
        stmt = select(md.Course).where(md.Course.id == course_id)
        res = await db.scalar(stmt)
        if res is None:
            return Response("⚠️ NO COURSE FOUND !!", status_code=404)
        await db.delete(res)
        return "✅ DELETED COURSE SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COURSEPOST 🟢

    @get(
        ["/post/{course_id:int}"],
        exclude_from_auth=True,
        description="Get all the posts of specific course ",
    )
    async def posts(
        self,
        db: AsyncSession,
        course_id: int = Parameter(description="ID of Course"),
    ) -> list[md.CoursePost]:
        res = await db.scalars(
            select(md.CoursePost).where(md.CoursePost.course_id == course_id)
        )
        ans = res._allrows()
        return ans

    @post(
        ["/post/{course_id:int}/add", "/post/{course_id:int}/{coursepost_id:int}/add"]
    )
    async def post_add(
        self,
        data: mv.Post,
        request: Request,
        db: AsyncSession,
        coursepost_id: Optional[int] = Parameter(
            description="ID of comment to reply to"
        ),
        course_id: int = Parameter(description="ID of Course to comment on"),
    ) -> mv.Post:
        user_id = request.user.get("user_id")
        if coursepost_id is not None:
            db.add(
                md.CoursePost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    coursepost_id=coursepost_id,
                    course_id=course_id,
                )
            )
        else:
            db.add(
                md.CoursePost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    course_id=course_id,
                )
            )
        return data

    @delete("/post/{post_id:int}/delete", status_code=201)
    async def post_delete(
        self,
        post_id: Annotated[int, Parameter(description="ID of Post to delete")],
        db: AsyncSession,
    ) -> str | Response:
        stmt = select(md.CoursePost).where(md.CoursePost.id == post_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO POST FOUND !!")
        await db.delete(res)
        return "✅ DELETED POST SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COURSELIST 🟢
    @get(["/list/all"], exclude_from_auth=True)
    async def lists_all(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[md.CourseList]:
        res = await db.scalars(
            select(md.CourseList).where(md.CourseList.view == "Public")
        )
        ans = res._allrows()
        return ans

    @get(["/list"])
    async def lists_user(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[md.CourseList]:
        # user_id = request.user.get("user_id")
        user_id = request.user["user_id"]
        res = await db.scalars(
            select(md.CourseList).where(md.CourseList.user_id == user_id)
        )
        ans = res._allrows()
        return ans

    @post(["/list/add"], media_type=MediaType.TEXT)
    async def list_add(
        self,
        data: mv.List,
        request: Request,
        db: AsyncSession,
    ) -> Any:
        try:
            await db.get_one(md.Course, data.course_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO COURSE FOUND !!")
        user_id = request.user.get("user_id")
        stmt = insert(md.CourseList).values(
            user_id=user_id, course_id=data.course_id, view=data.view.value
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ LIST ENTRY ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @delete("/list/{course_id:int}/delete", status_code=200, media_type=MediaType.TEXT)
    async def list_delete(
        self,
        request: Request,
        db: AsyncSession,
        course_id: int = Parameter(description="ID of Course in your list to delete"),
    ) -> Any:
        try:
            await db.get_one(md.Course, course_id)
        except NoResultFound:
            return Response("⚠️ NO COURSE FOUND !!", status_code=404)
        user_id = request.user.get("user_id")
        stmt = (
            select(md.CourseList)
            .where(md.CourseList.course_id == course_id)
            .and_(md.CourseList.user_id == user_id)
        )
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO LIST ENTRY FOUND !!")
        await db.delete(res)
        return "✅ DELETED LIST ENTRY SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COURSELIKES 🟢
    @post("/likes", media_type=MediaType.TEXT)
    async def likes_add(
        self, course_id: int, request: Request, db: AsyncSession
    ) -> str | Response:
        try:
            await db.get_one(md.Course, course_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO COURSE FOUND !!")
        user_id = request.user.get("user_id")
        try:
            await db.scalar(
                insert(md.CourseLikes).values(user_id=user_id, course_id=course_id)
            )
        except IntegrityError:
            return Response("⚠️ ALREADY LIKED !!", status_code=400)
        stmt = (
            update(md.Course)
            .where(md.Course.id == course_id)
            .values(likes=md.Course.likes + 1)
        )
        await db.execute(stmt)
        return f"✅ LIKED COURSE {course_id}"

    @get("/likes/ranking", exclude_from_auth=True, cache=600)
    async def likes_ranking(self, db: AsyncSession) -> list[md.Course]:
        stmt = select(md.Course).order_by(desc(md.Course.likes))
        res = await db.scalars(stmt)
        return res._allrows()


# ..........................................................................................     COLLEGE CONTROLLER 🔰


class collegecontroller(Controller):
    path = "/college"
    tags = ["🟢   Colleges"]

    @get("/", exclude_from_auth=True)
    async def colleges(self, db: AsyncSession) -> list[md.College]:
        res = await db.scalars(select(md.College))
        return res._allrows()

    @post("/add", guards=[check_admin], media_type=MediaType.TEXT)
    async def college_add(
        self,
        db: AsyncSession,
        data: mv.College = Body(title="College", default=1, examples=[1]),
    ) -> Any:
        try:
            data.rank = int(data.rank)
        except ValueError:
            raise ValidationException("⚠️ Rank can only be integer")
        if data.rank < 1:
            raise ValidationException("⚠️ Rank can't be less than than 1")
        stmt = insert(md.College).values(
            name=data.name,
            rank=data.rank,
            email=data.email,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ COLLEGE ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @patch("/update/{college_id:int}", guards=[check_admin])
    async def college_update(
        self,
        college_id: int,
        db: AsyncSession,
        data: dict = Parameter(description=f"DEMO SCHEMA  =  {mv.College.__slots__}"),
    ) -> Any:
        stmt = update(md.College).where(md.College.id == college_id).values(**data)
        await db.execute(stmt)
        return data

    @delete(
        "/delete/{college_id:int}",
        status_code=200,
        guards=[check_admin],
        media_type=MediaType.TEXT,
    )
    async def college_delete(
        self,
        db: AsyncSession,
        college_id: int = Parameter(description="ID of College to delete"),
    ) -> str | Response:
        stmt = select(md.College).where(md.College.id == college_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO COLLEGE FOUND !!")
        await db.delete(res)
        return "✅ DELETED COLLEGE SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COLLEGEPOST 🟢

    @get(
        ["/post/{college_id:int}"],
        exclude_from_auth=True,
        description="Get all the posts of specific college ",
    )
    async def posts(
        self,
        db: AsyncSession,
        college_id: int = Parameter(description="ID of Course"),
    ) -> list[md.CollegePost]:
        res = await db.scalars(
            select(md.CollegePost).where(md.CollegePost.college_id == college_id)
        )
        ans = res._allrows()
        return ans

    @post(
        [
            "/post/{college_id:int}/add",
            "/post/{college_id:int}/{collegepost_id:int}/add",
        ]
    )
    async def post_add(
        self,
        data: mv.Post,
        request: Request,
        db: AsyncSession,
        collegepost_id: Optional[int] = Parameter(
            description="ID of comment to reply to"
        ),
        college_id: int = Parameter(description="ID of College to comment on"),
    ) -> mv.Post:
        user_id = request.user.get("user_id")
        if collegepost_id is not None:
            db.add(
                md.CollegePost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    collegepost_id=collegepost_id,
                    college_id=college_id,
                )
            )
        else:
            db.add(
                md.CollegePost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    college_id=college_id,
                )
            )
        return data

    @delete("/post/{post_id:int}/delete", status_code=201, media_type=MediaType.TEXT)
    async def post_delete(
        self,
        post_id: Annotated[int, Parameter(description="ID of Post to delete")],
        db: AsyncSession,
    ) -> str | Response:
        stmt = select(md.CollegePost).where(md.CollegePost.id == post_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO POST FOUND !!")
        await db.delete(res)
        return "✅ DELETED POST SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COLLEGELIST 🟢
    @get(["/list/all"], exclude_from_auth=True)
    async def lists_all(
        self,
        db: AsyncSession,
    ) -> list[md.CollegeList]:
        res = await db.scalars(
            select(md.CollegeList).where(md.CollegeList.view == "Public")
        )
        ans = res._allrows()
        return ans

    @get(["/list"])
    async def lists_user(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[md.CollegeList]:
        user_id = request.user.get("user_id")
        res = await db.scalars(
            select(md.CollegeList).where(md.CollegeList.user_id == user_id)
        )
        ans = res._allrows()
        return ans

    @post(["/list/add"], media_type=MediaType.TEXT)
    async def list_add(
        self,
        data: mv.List,
        request: Request,
        db: AsyncSession,
    ) -> Any:
        try:
            await db.get_one(md.College, data.course_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO COLLEGE FOUND !!")
        user_id = request.user.get("user_id")
        stmt = insert(md.CollegeList).values(
            user_id=user_id, college_id=data.course_id, view=data.view.value
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ LIST ENTRY ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @delete("/list/{college_id:int}/delete", status_code=200, media_type=MediaType.TEXT)
    async def list_delete(
        self,
        request: Request,
        db: AsyncSession,
        college_id: int = Parameter(description="ID of College in your list to delete"),
    ) -> Any:
        try:
            await db.get_one(md.College, college_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO COLLEGE FOUND !!")
        user_id = request.user.get("user_id")
        stmt = (
            select(md.CollegeList)
            .where(md.CollegeList.college_id == college_id)
            .and_(md.CollegeList.user_id == user_id)
        )
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO LIST ENTRY FOUND !!")
        await db.delete(res)
        return "✅ DELETED LIST ENTRY SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   COLLEGELIKES 🟢
    @post("/likes", media_type=MediaType.TEXT)
    async def likes_add(
        self, college_id: int, request: Request, db: AsyncSession
    ) -> str | Response:
        try:
            await db.get_one(md.College, college_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO COLLEGE FOUND !!")
        user_id = request.user.get("user_id")
        try:
            await db.scalar(
                insert(md.CollegeLikes).values(user_id=user_id, college_id=college_id)
            )
        except IntegrityError:
            return Response("⚠️ ALREADY LIKED !!", status_code=400)
        stmt = (
            update(md.College)
            .where(md.College.id == college_id)
            .values(likes=md.College.likes + 1)
        )
        await db.execute(stmt)
        return f"✅ LIKED COLLEGE {college_id}"

    @get("/likes/ranking", exclude_from_auth=True, cache=600)
    async def likes_ranking(self, db: AsyncSession) -> list[md.College]:
        stmt = select(md.College).order_by(desc(md.College.likes))
        res = await db.scalars(stmt)
        return res._allrows()


# ..........................................................................................     EXAM CONTROLLER 🔰


class examcontroller(Controller):
    path = "/exam"
    tags = ["🟢   Exams"]

    @get("/", exclude_from_auth=True)
    async def exams(self, db: AsyncSession) -> Sequence[md.Exam]:
        res = await db.scalars(select(md.Exam))
        ans = res.all()
        return ans

    @post("/add", guards=[check_admin], media_type=MediaType.TEXT)
    async def exam_add(self, data: mv.Exam, db: AsyncSession) -> str | Response:
        stmt = insert(md.Exam).values(
            name=data.name, elig=data.elig, syllabus=data.syllabus, fee=data.fee
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ EXAM ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @patch("/update/{exam_id:int}", guards=[check_admin])
    async def exam_update(
        self,
        exam_id: int,
        db: AsyncSession,
        data: dict = Parameter(description=f"DEMO SCHEMA  =  {mv.Exam.__slots__}"),
    ) -> Any:
        stmt = update(md.Exam).where(md.Exam.id == exam_id).values(**data)
        await db.execute(stmt)
        return data

    @delete(
        "/delete/{exam_id:int}",
        status_code=200,
        guards=[check_admin],
        media_type=MediaType.TEXT,
    )
    async def exam_delete(
        self,
        exam_id: Annotated[int, Parameter(description="ID of Exam to delete")],
        db: AsyncSession,
    ) -> str | Response:
        stmt = select(md.Exam).where(md.Exam.id == exam_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO EXAM FOUND !!")
        await db.delete(res)
        return "✅ DELETED SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   EXAMPOST 🟢

    @get(
        ["/post/{exam_id:int}"],
        exclude_from_auth=True,
        description="Get all the posts of specific college ",
    )
    async def posts(
        self,
        db: AsyncSession,
        exam_id: int = Parameter(description="ID of Course"),
    ) -> list[md.ExamPost]:
        res = await db.scalars(
            select(md.ExamPost).where(md.ExamPost.exam_id == exam_id)
        )
        ans = res._allrows()
        return ans

    @post(
        [
            "/post/{exam_id:int}/add",
            "/post/{exam_id:int}/{exampost_id:int}/add",
        ]
    )
    async def post_add(
        self,
        data: mv.Post,
        request: Request,
        db: AsyncSession,
        exampost_id: Optional[int] = Parameter(description="ID of comment to reply to"),
        exam_id: int = Parameter(description="ID of Exam to comment on"),
    ) -> mv.Post:
        user_id = request.user.get("user_id")
        if exam_id is not None:
            db.add(
                md.ExamPost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    exampost_id=exampost_id,
                    exam_id=exam_id,
                )
            )
        else:
            db.add(
                md.ExamPost(
                    title=data.title,
                    body=data.body,
                    user_id=user_id,
                    exam_id=exam_id,
                )
            )
        return data

    @delete("/post/{post_id:int}/delete", status_code=201, media_type=MediaType.TEXT)
    async def post_delete(
        self,
        post_id: Annotated[int, Parameter(description="ID of Post to delete")],
        db: AsyncSession,
    ) -> str | Response:
        stmt = select(md.ExamPost).where(md.ExamPost.id == post_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO POST FOUND !!")
        await db.delete(res)
        return "✅ DELETED POST SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   EXAMLIST 🟢
    @get(["/list/all"], exclude_from_auth=True)
    async def lists_all(
        self,
        db: AsyncSession,
    ) -> list[md.ExamList]:
        res = await db.scalars(select(md.ExamList).where(md.ExamList.view == "Public"))
        ans = res._allrows()
        return ans

    @get(["/list"])
    async def lists_user(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[md.ExamList]:
        user_id = request.user.get("user_id")
        res = await db.scalars(
            select(md.ExamList).where(md.ExamList.user_id == user_id)
        )
        ans = res._allrows()
        return ans

    @post(["/list/add"], media_type=MediaType.TEXT)
    async def list_add(
        self,
        data: mv.List,
        request: Request,
        db: AsyncSession,
    ) -> Any:
        try:
            await db.get_one(md.Exam, data.course_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO EXAM FOUND !!")
        user_id = request.user.get("user_id")
        stmt = insert(md.ExamList).values(
            user_id=user_id, exam_id=data.course_id, view=data.view.value
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ LIST ENTRY ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @delete("/list/{exam_id:int}/delete", status_code=200, media_type=MediaType.TEXT)
    async def list_delete(
        self,
        request: Request,
        db: AsyncSession,
        exam_id: int = Parameter(description="ID of Exam in your list to delete"),
    ) -> Any:
        try:
            await db.get_one(md.Exam, exam_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO EXAM FOUND !!")
        user_id = request.user.get("user_id")
        stmt = (
            select(md.ExamList)
            .where(md.ExamList.exam_id == exam_id)
            .and_(md.ExamList.user_id == user_id)
        )
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO LIST ENTRY FOUND !!")
        await db.delete(res)
        return "✅ DELETED LIST ENTRY SUCCESSFULLY !!"

    # ------------------------------------------------------------------->   EXAMLIKES 🟢
    @post("/likes", media_type=MediaType.TEXT)
    async def likes_add(
        self, exam_id: int, request: Request, db: AsyncSession
    ) -> str | Response:
        try:
            await db.get_one(md.Exam, exam_id)
        except NoResultFound:
            raise NotFoundException("⚠️ NO EXAM FOUND !!")
        user_id = request.user.get("user_id")
        try:
            await db.scalar(
                insert(md.ExamLikes).values(user_id=user_id, exam_id=exam_id)
            )
        except IntegrityError:
            return Response("⚠️ ALREADY LIKED !!", status_code=400)
        stmt = (
            update(md.Exam).where(md.Exam.id == exam_id).values(likes=md.Exam.likes + 1)
        )
        await db.execute(stmt)
        return f"✅ LIKED EXAM {exam_id}"

    @get("/likes/ranking", exclude_from_auth=True, cache=600)
    async def likes_ranking(self, db: AsyncSession) -> list[md.Exam]:
        stmt = select(md.Exam).order_by(desc(md.Exam.likes))
        res = await db.scalars(stmt)
        return res._allrows()


# ..........................................................................................     ACADEMICS CONTROLLER 🔰


class academicscontroller(Controller):
    path = "/academics"
    tags = ["🟢   Academics"]

    @get("/", exclude_from_auth=True, cache=CACHE_FOREVER)
    async def academics(self, db: AsyncSession) -> Sequence[md.Academics]:
        res = await db.scalars(select(md.Academics))
        ans = res.all()
        return ans

    @post("/add", guards=[check_admin], media_type=MediaType.TEXT)
    async def add(self, data: mv.Academics, db: AsyncSession) -> str | Response:
        stmt = insert(md.Academics).values(
            course_fee=data.course_fee,
            cutoff_rank=data.cutoff_rank,
            course_id=data.course_id,
            college_id=data.college_id,
            exam_id=data.exam_id,
        )
        try:
            await db.scalar(stmt)
        except Exception:
            return Response("⚠️ ACADEMICS ALREADY EXISTS !!", status_code=400)
        return "✅ ADDED SUCCESSFULLY !!"

    @delete("/delete/{academics_id:int}", status_code=200, guards=[check_admin])
    async def delete(self, academics_id: int, db: AsyncSession) -> str | Response:
        stmt = select(md.Academics).where(md.Academics.id == academics_id)
        res = await db.scalar(stmt)
        if res is None:
            raise NotFoundException("⚠️ NO ACADEMICS FOUND !!")
        await db.delete(res)
        return "✅ DELETED SUCCESSFULLY !!"

    @get("/colleges-from-course", exclude_from_auth=True, cache=CACHE_FOREVER)
    async def CollegesFromCourse(
        self,
        db: AsyncSession,
        course_id: int = Parameter(description="Get all Colleges offering this Course"),
    ) -> list[md.College]:
        # ) -> list[Any]:
        # stmt = select(md.College).where(
        #     md.College.id.in_(
        #         select(md.Academics.college_id).where(
        #             md.Academics.course_id == course_id
        #         )
        #     )
        # )
        # -----------------IN CLAUSE VS JOIN
        stmt = (
            select(md.College).join(
                md.Academics,
                (md.Academics.college_id == md.College.id)
                & (md.Academics.course_id == course_id),
            )
            # .where(md.Academics.course_id == course_id)
        )
        # print(stmt)
        res = await db.scalars(stmt)
        ans = res._allrows()
        return ans

    @get("/academics-from-exam", exclude_from_auth=True, cache=CACHE_FOREVER)
    async def AcademicsFromExam(
        self,
        db: AsyncSession,
        exam_id: int = Parameter(
            description="Get all College & Courses accepting this Exam"
        ),
    ) -> list[dict]:
        stmt = (
            select(
                md.College.id.label("College_id"),
                md.College.name.label("College"),
                md.Course.id.label("Course_id"),
                md.Course.name.label("Course"),
            )
            .join(
                md.Academics,
                (md.Academics.college_id == md.College.id),
                # & (md.Academics.exam_id == exam_id),
            )
            .join(
                md.Course,
                (md.Academics.course_id == md.Course.id)
                & (md.Academics.exam_id == exam_id),
            )
        )
        res = await db.execute(stmt)
        ans = res.mappings()
        ans = [dict(i) for i in ans]
        return ans


# -----------------------------------------------------------------------------> EXCEPTION HANDLER
def exception_handler(_: Request, exc: Exception) -> Response:
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "⚠️ SOME ERROR OCCURED")
    return Response(
        media_type=MediaType.TEXT,
        content=detail,
        status_code=status_code,
    )


# -----------------------------------------------------------------------------> MAIN APP


app = Litestar(
    route_handlers=[
        usercontroller,
        coursecontroller,
        collegecontroller,
        examcontroller,
        academicscontroller,
    ],
    dependencies={"db": Provide(provide_transaction)},
    lifespan=[db_connection],
    plugins=[SQLAlchemySerializationPlugin()],
    on_app_init=[jwt_cookie_auth.on_app_init],
    debug=True,
    exception_handlers={
        ValidationException: exception_handler,
        NotAuthorizedException: exception_handler,
        NotFoundException: exception_handler,
    },
    openapi_config=OpenAPIConfig(
        title="AcademicWorld", version="", root_schema_site="rapidoc"
    ),
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app", host="localhost", port=8080, reload=True)
