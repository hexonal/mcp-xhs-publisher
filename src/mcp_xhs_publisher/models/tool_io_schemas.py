"""
MCP小红书工具输入输出模型

定义所有MCP小红书工具的输入和输出模型
"""
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class LoginInput(BaseModel):
    """登录输入参数"""
    account: str = Field(..., description="小红书账号标识")
    cookie_dir: Optional[str] = Field(None, description="cookie存储目录")
    sign_url: Optional[str] = Field(None, description="签名服务URL")


class LoginResponse(BaseModel):
    """登录结果响应"""
    status: str = Field(..., description="状态：success 或 error")
    message: str = Field(..., description="状态说明")
    user_info: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    error: Optional[str] = Field(None, description="错误信息")
    data: Optional[Dict[str, Any]] = Field(None, description="其他数据")


class PhoneLoginInput(BaseModel):
    """手机登录输入参数"""
    phone: str = Field(..., description="手机号码")
    code: Optional[str] = Field(None, description="短信验证码")
    area_code: str = Field("+86", description="国家/地区代码")


class CheckLoginStatusInput(BaseModel):
    """检查登录状态输入参数"""
    account: str = Field(..., description="小红书账号标识")


class PublishTextInput(BaseModel):
    """文本笔记发布输入参数"""
    content: str = Field(..., description="笔记文本内容")
    topics: Optional[List[str]] = Field(None, description="话题关键词列表")


class PublishImageInput(BaseModel):
    """图文笔记发布输入参数"""
    content: str = Field(..., description="笔记文本内容")
    image_paths: List[str] = Field(..., description="图片路径列表，支持本地路径和https链接")
    topics: Optional[List[str]] = Field(None, description="话题关键词列表")


class PublishVideoInput(BaseModel):
    """视频笔记发布输入参数"""
    content: str = Field(..., description="笔记文本内容")
    video_path: str = Field(..., description="视频文件路径")
    cover_path: Optional[str] = Field(None, description="封面图片路径")
    topics: Optional[List[str]] = Field(None, description="话题关键词列表")


class PublishResponse(BaseModel):
    """发布结果响应模型"""
    status: str = Field(..., description="状态：success 或 error")
    type: str = Field(..., description="笔记类型：text, image 或 video")
    result: Optional[Dict[str, Any]] = Field(None, description="发布结果数据")
    error: Optional[str] = Field(None, description="错误信息") 