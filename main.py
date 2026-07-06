from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

app = FastAPI(title="API hệ thống khóa học trực tuyến")

courses_db = [
    {"id": 1, "course_name": "FastAPI Masterclass", "duration_hours": 32, "price": 1500000, "status": "active", "created_at": "2026-07-01T02:00:00Z"},
    {"id": 2, "course_name": "NextJS Next-Level", "duration_hours": 45, "price": 1800000, "status": "active", "created_at": "2026-07-01T03:15:00Z"}
]

class CourseCreateSchema(BaseModel):
    course_name: str = Field
    duration_hours: int = Field
    price: int = Field

def create_response(req: Request, status_code: int, message: str, data: Optional[Any] = None, error: Optional[str] = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": req.url.path
        }
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return create_response(
        req=request,
        status_code=exc.status_code,
        message=getattr(exc, "custom_message", "Đã xảy ra lỗi hệ thống!"),
        error=exc.detail
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_response(
        req=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Lỗi: Dữ liệu đầu vào không hợp lệ!",
        error=str(exc.errors())
    )

@app.get("/courses", tags=["Courses"])
def get_all_courses(req: Request):
    return create_response(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách khóa học thành công!",
        data=courses_db
    )

@app.post("/courses", tags=["Courses"])
def create_course(req: Request, course_in: CourseCreateSchema):
    for course in courses_db:
        if course["course_name"] == course_in.course_name:
            exc = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ERR-EDU-01: Course name duplicates an existing record in memory array."
            )
            setattr(exc, "custom_message", "Lỗi: Tên khóa học này đã tồn tại trong danh mục đào tạo!")
            raise exc
    new_id = max([c["id"] for c in courses_db]) + 1 if courses_db else 1
    new_course = {
        "id": new_id,
        "course_name": course_in.course_name,
        "duration_hours": course_in.duration_hours,
        "price": course_in.price,
        "status": "active",
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    courses_db.append(new_course)
    return create_response(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Tạo mới khóa học thành công!",
        data=new_course
    )

@app.delete("/courses/{course_id}", tags=["Courses"])
def delete_course(req: Request, course_id: int):
    target_course = None
    for course in courses_db:
        if course["id"] == course_id:
            target_course = course
            break
    if not target_course:
        exc = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR-EDU-02: Target course ID can not be found."
        )
        setattr(exc, "custom_message", "Lỗi: Không tìm thấy mã khóa học yêu cầu để xóa!")
        raise exc
    courses_db.remove(target_course)
    return create_response(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Xóa khóa học thành công!"
    )