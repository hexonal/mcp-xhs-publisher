"""
小红书发布工具执行器

实现MCP工具发布功能，遵循MCP工具指南规范
"""

from ..models.tool_io_schemas import (
    PublishImageInput,
    PublishResponse,
    PublishTextInput,
    PublishVideoInput,
)
from ..services.xhs_client import XhsApiClient
from ..util.logging import log_error


class PublishExecutor:
    """
    小红书发布工具执行器

    负责实现MCP工具的具体执行逻辑，包括文本、图文和视频笔记的发布
    使用单一客户端实例
    """

    def __init__(self):
        """初始化执行器，创建单一客户端实例"""
        try:
            # 直接从环境变量创建客户端实例
            self.client = XhsApiClient.build_from_env()
        except Exception as e:
            log_error(f"创建客户端实例失败: {e}")
            raise

    def publish_text(self, params: PublishTextInput) -> PublishResponse:
        """
        发布纯文本笔记

        Args:
            params: 文本笔记参数

        Returns:
            PublishResponse: 发布结果
        """
        try:
            response = self.client.create_text_note(
                content=params.content, topics=params.topics or []
            )
            if response.get("status") == "success":
                result = response.get("result", {}) or {}
                note_id = result.get("id") or result.get("note_id") or ""
                publish_time = result.get("create_time") or result.get("time") or ""
                return PublishResponse(
                    status="success",
                    message="文本笔记发布成功",
                    note_id=note_id,
                    note_type="text",
                    publish_time=publish_time,
                )
            else:
                return PublishResponse(
                    status="error",
                    message="文本笔记发布失败",
                    error=response.get("error", "未知错误"),
                )
        except Exception as e:
            log_error(f"发布文本笔记出错: {e}")
            return PublishResponse(
                status="error", message="发布文本笔记时发生异常", error=str(e)
            )

    def publish_image(self, params: PublishImageInput) -> PublishResponse:
        """
        发布图文笔记

        Args:
            params: 图文笔记参数

        Returns:
            PublishResponse: 发布结果
        """
        try:
            response = self.client.create_image_note(
                content=params.content,
                image_paths=params.image_paths,
                topics=params.topics or [],
            )
            if response.get("status") == "success":
                result = response.get("result", {}) or {}
                note_id = result.get("id") or result.get("note_id") or ""
                publish_time = result.get("create_time") or result.get("time") or ""
                images = result.get("images") or []
                image_count = len(images) if images else len(params.image_paths)
                return PublishResponse(
                    status="success",
                    message="图文笔记发布成功",
                    note_id=note_id,
                    note_type="image",
                    publish_time=publish_time,
                    image_count=image_count,
                )
            else:
                return PublishResponse(
                    status="error",
                    message="图文笔记发布失败",
                    error=response.get("error", "未知错误"),
                )
        except Exception as e:
            log_error(f"发布图文笔记出错: {e}")
            return PublishResponse(
                status="error", message="发布图文笔记时发生异常", error=str(e)
            )

    def publish_video(self, params: PublishVideoInput) -> PublishResponse:
        """
        发布视频笔记

        Args:
            params: 视频笔记参数

        Returns:
            PublishResponse: 发布结果
        """
        try:
            response = self.client.create_video_note(
                content=params.content,
                video_path=params.video_path,
                cover_path=params.cover_path,
                topics=params.topics or [],
            )
            if response.get("status") == "success":
                result = response.get("result", {}) or {}
                note_id = result.get("id") or result.get("note_id") or ""
                publish_time = result.get("create_time") or result.get("time") or ""
                return PublishResponse(
                    status="success",
                    message="视频笔记发布成功",
                    note_id=note_id,
                    note_type="video",
                    publish_time=publish_time,
                )
            else:
                return PublishResponse(
                    status="error",
                    message="视频笔记发布失败",
                    error=response.get("error", "未知错误"),
                )
        except Exception as e:
            log_error(f"发布视频笔记出错: {e}")
            return PublishResponse(
                status="error", message="发布视频笔记时发生异常", error=str(e)
            )
