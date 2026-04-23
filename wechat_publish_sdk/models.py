"""数据模型定义"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PublishRequest:
    """发布文章请求"""
    account: str = field(default="")
    title: str = field(default="")
    content: str = field(default="")
    content_format: str = field(default="markdown")
    theme: Optional[str] = field(default=None)
    thumb_media_id: Optional[str] = field(default=None)
    show_cover_pic: int = field(default=1)
    author: Optional[str] = field(default=None)
    digest: Optional[str] = field(default=None)
    need_open_comment: int = field(default=1)
    only_fans_can_comment: int = field(default=0)


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    message: str
    draft_id: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class UploadRequest:
    """上传素材请求"""
    account: str
    file_path: str


@dataclass
class UploadResult:
    """上传结果"""
    success: bool
    message: str
    media_id: Optional[str] = None
    url: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class MaterialItem:
    """素材项"""
    media_id: str
    name: str
    url: str
    update_time: str
    type: str


@dataclass
class MaterialsListResult:
    """素材列表结果"""
    success: bool
    message: str
    total_count: int = 0
    item_count: int = 0
    items: List[MaterialItem] = None
    error_code: Optional[str] = None


@dataclass
class RenderRequest:
    """渲染请求"""
    content: str
    theme: str = "default"
    enable_highlight: bool = True


@dataclass
class RenderResult:
    """渲染结果"""
    success: bool
    html: str = ""
    message: str = ""
    error_code: Optional[str] = None
