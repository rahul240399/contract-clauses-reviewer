"""Persistence adapters implementing the ReviewRepository port."""

from .sqlite_repo import SQLiteReviewRepository

__all__ = ["SQLiteReviewRepository"]
