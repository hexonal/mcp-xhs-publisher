"""
基础数据模型定义

包含项目中常用的基础数据模型和共享结构
"""
from typing import Dict, Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """API响应的基础模型"""
    status: str = Field(..., description="响应状态，success或error")
    type: str = Field(..., description="操作类型")
    
    class Config:
        arbitrary_types_allowed = True


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    result: Dict[str, Any] = Field(..., description="操作结果")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    error: str = Field(..., description="错误信息") 