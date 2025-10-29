"""PostgreSQL-backed ChatKit Store implementation."""

from datetime import datetime
from typing import Any

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, TextContentPart, Thread, ThreadItem, ThreadMetadata, UserMessageItem
from sqlalchemy.orm import Session

from app.db_models import Thread as ThreadDB
from app.db_models import ThreadItem as ThreadItemDB


class PostgreSQLStore(Store[dict[str, Any]]):
    """PostgreSQL-backed Store for ChatKit chat history and metadata."""

    def __init__(self, db_session: Session):
        self.db = db_session

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """Return thread metadata without any embedded items."""
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    # -- Thread metadata -------------------------------------------------
    async def load_thread(self, thread_id: str, context: dict[str, Any]) -> ThreadMetadata:
        thread_db = self.db.query(ThreadDB).filter(ThreadDB.id == thread_id).first()
        if not thread_db:
            raise NotFoundError(f"Thread {thread_id} not found")

        return ThreadMetadata(
            id=thread_db.id,
            created_at=thread_db.created_at,
            title=thread_db.title,
        )

    async def save_thread(self, thread: ThreadMetadata, context: dict[str, Any]) -> None:
        metadata = self._coerce_thread_metadata(thread)
        thread_db = self.db.query(ThreadDB).filter(ThreadDB.id == metadata.id).first()

        if thread_db:
            thread_db.title = metadata.title
            thread_db.updated_at = datetime.utcnow()
        else:
            thread_db = ThreadDB(
                id=metadata.id,
                title=metadata.title,
                created_at=metadata.created_at or datetime.utcnow(),
            )
            self.db.add(thread_db)

        self.db.commit()

    async def load_threads(
        self,
        limit: int,
        after: str | None,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        query = self.db.query(ThreadDB)

        if after:
            after_thread = self.db.query(ThreadDB).filter(ThreadDB.id == after).first()
            if after_thread:
                if order == "desc":
                    query = query.filter(ThreadDB.created_at < after_thread.created_at)
                else:
                    query = query.filter(ThreadDB.created_at > after_thread.created_at)

        if order == "desc":
            threads = query.order_by(ThreadDB.created_at.desc()).limit(limit + 1).all()
        else:
            threads = query.order_by(ThreadDB.created_at.asc()).limit(limit + 1).all()

        has_more = len(threads) > limit
        threads = threads[:limit]

        thread_metas = [
            ThreadMetadata(id=t.id, created_at=t.created_at, title=t.title)
            for t in threads
        ]

        next_after = threads[-1].id if has_more and threads else None
        return Page(data=thread_metas, has_more=has_more, after=next_after)

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        self.db.query(ThreadDB).filter(ThreadDB.id == thread_id).delete()
        self.db.commit()

    # -- Thread items ----------------------------------------------------
    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: dict[str, Any],
    ) -> Page[ThreadItem]:
        query = self.db.query(ThreadItemDB).filter(ThreadItemDB.thread_id == thread_id)

        if after:
            after_item = self.db.query(ThreadItemDB).filter(ThreadItemDB.id == after).first()
            if after_item:
                if order == "desc":
                    query = query.filter(ThreadItemDB.created_at < after_item.created_at)
                else:
                    query = query.filter(ThreadItemDB.created_at > after_item.created_at)

        if order == "desc":
            items_db = query.order_by(ThreadItemDB.created_at.desc()).limit(limit + 1).all()
        else:
            items_db = query.order_by(ThreadItemDB.created_at.asc()).limit(limit + 1).all()

        has_more = len(items_db) > limit
        items_db = items_db[:limit]

        items = [self._db_item_to_model(item_db) for item_db in items_db]
        next_after = items_db[-1].id if has_more and items_db else None

        return Page(data=items, has_more=has_more, after=next_after)

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        item_db = ThreadItemDB(
            id=item.id,
            thread_id=thread_id,
            role=getattr(item, "role", "assistant"),
            content=self._item_to_content(item),
            item_type=item.__class__.__name__,
            metadata=item.model_dump() if hasattr(item, "model_dump") else {},
        )
        self.db.add(item_db)
        self.db.commit()

    async def save_item(self, thread_id: str, item: ThreadItem, context: dict[str, Any]) -> None:
        item_db = self.db.query(ThreadItemDB).filter(ThreadItemDB.id == item.id).first()

        if item_db:
            item_db.content = self._item_to_content(item)
            item_db.metadata = item.model_dump() if hasattr(item, "model_dump") else {}
            item_db.updated_at = datetime.utcnow()
        else:
            item_db = ThreadItemDB(
                id=item.id,
                thread_id=thread_id,
                role=getattr(item, "role", "assistant"),
                content=self._item_to_content(item),
                item_type=item.__class__.__name__,
                metadata=item.model_dump() if hasattr(item, "model_dump") else {},
            )
            self.db.add(item_db)

        self.db.commit()

    async def load_item(self, thread_id: str, item_id: str, context: dict[str, Any]) -> ThreadItem:
        item_db = self.db.query(ThreadItemDB).filter(
            ThreadItemDB.id == item_id,
            ThreadItemDB.thread_id == thread_id
        ).first()

        if not item_db:
            raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")

        return self._db_item_to_model(item_db)

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        self.db.query(ThreadItemDB).filter(
            ThreadItemDB.id == item_id,
            ThreadItemDB.thread_id == thread_id
        ).delete()
        self.db.commit()

    # -- Files -----------------------------------------------------------
    async def save_attachment(
        self,
        attachment: Attachment,
        context: dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            "PostgreSQLStore does not support attachments yet."
        )

    async def load_attachment(
        self,
        attachment_id: str,
        context: dict[str, Any],
    ) -> Attachment:
        raise NotImplementedError(
            "PostgreSQLStore does not support attachments yet."
        )

    async def delete_attachment(self, attachment_id: str, context: dict[str, Any]) -> None:
        raise NotImplementedError(
            "PostgreSQLStore does not support attachments yet."
        )

    # -- Helpers ---------------------------------------------------------
    def _item_to_content(self, item: ThreadItem) -> str:
        """Extract text content from ThreadItem."""
        if hasattr(item, "content"):
            if isinstance(item.content, str):
                return item.content
            if isinstance(item.content, list):
                # UserMessageItem has content as list of content parts
                return "".join(
                    getattr(part, "text", "")
                    for part in item.content
                    if hasattr(part, "text")
                )
        return ""

    def _db_item_to_model(self, item_db: ThreadItemDB) -> ThreadItem:
        """Convert database model back to ThreadItem."""
        if item_db.metadata:
            return UserMessageItem(**item_db.metadata)

        # Fallback
        return UserMessageItem(
            id=item_db.id,
            content=[TextContentPart(text=item_db.content or "")],
            created_at=item_db.created_at,
        )
