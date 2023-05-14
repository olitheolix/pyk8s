"""Pydantic models"""
from pathlib import Path
from typing import Any, List

from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration."""
    k8s_session: Any
    k8s_url: str
    k8s_creds_path: Path


class K8sNamespaces(BaseModel):
    """Application configuration."""
    namespaces: List[str]
