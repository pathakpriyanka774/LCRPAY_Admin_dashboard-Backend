from typing import Type, List, Optional, Dict, Any, Callable
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import inspect, desc, asc, or_, and_
from pydantic import BaseModel, create_model
from datetime import datetime
from core.database import get_db
from core.auth import require_admin
import csv
import io


class FieldMetadata(BaseModel):
    name: str
    type: str
    required: bool = False
    readonly: bool = False
    unique: bool = False
    choices: Optional[List[str]] = None
    references: Optional[str] = None
    default: Any = None


class CRUDGenerator:
    """Generic CRUD API generator for SQLAlchemy models"""

    @staticmethod
    def get_model_fields(model: Type) -> List[FieldMetadata]:
        """Extract field metadata from SQLAlchemy model including relationships and enums"""
        mapper = inspect(model)
        fields = []

        # Extract column fields
        for column in mapper.columns:
            field_type = "string"
            choices = None

            # Determine field type
            col_type = str(column.type)
            col_type_lower = col_type.lower()
            
            # Check for Enum types first
            if hasattr(column.type, 'enums'):
                field_type = "enum"
                choices = list(column.type.enums)
            elif "integer" in col_type_lower or "serial" in col_type_lower:
                field_type = "integer"
            elif "boolean" in col_type_lower or "bool" in col_type_lower:
                field_type = "boolean"
            elif "decimal" in col_type_lower or "numeric" in col_type_lower:
                field_type = "decimal"
            elif "timestamp" in col_type_lower or "datetime" in col_type_lower or "date" in col_type_lower:
                field_type = "timestamp"
            elif "text" in col_type_lower:
                field_type = "text"
            elif "varchar" in col_type_lower or "string" in col_type_lower or "char" in col_type_lower:
                field_type = "string"

            # Check for foreign keys
            fk_reference = None
            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                fk_reference = fk.column.table.name

            fields.append(FieldMetadata(
                name=column.name,
                type=field_type,
                required=not column.nullable and column.default is None and not column.primary_key,
                readonly=column.primary_key or column.server_default is not None,
                unique=column.unique or column.primary_key,
                choices=choices,
                references=fk_reference,
                default=column.default.arg if column.default else None
            ))

        # Add relationship fields
        for relationship in mapper.relationships:
            fields.append(FieldMetadata(
                name=relationship.key,
                type="relationship",
                references=relationship.mapper.class_.__tablename__,
                readonly=True
            ))

        return fields

    @staticmethod
    def apply_filters(query, model: Type, filters: Dict[str, Any]):
        """Apply dynamic filters to query"""
        for key, value in filters.items():
            if value is None or value == "":
                continue

            # Handle comparison operators
            if key.endswith("__gt"):
                field = key.replace("__gt", "")
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) > value)
            elif key.endswith("__gte"):
                field = key.replace("__gte", "")
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) >= value)
            elif key.endswith("__lt"):
                field = key.replace("__lt", "")
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) < value)
            elif key.endswith("__lte"):
                field = key.replace("__lte", "")
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) <= value)
            elif key.endswith("__like"):
                field = key.replace("__like", "")
                if hasattr(model, field):
                    query = query.filter(getattr(model, field).like(f"%{value}%"))
            elif key.endswith("__in"):
                field = key.replace("__in", "")
                if hasattr(model, field):
                    values = value.split(",") if isinstance(value, str) else value
                    query = query.filter(getattr(model, field).in_(values))
            else:
                # Exact match
                if hasattr(model, key):
                    query = query.filter(getattr(model, key) == value)

        return query

    @staticmethod
    def apply_search(query, model: Type, search: str, fields: List[FieldMetadata]):
        """Apply search across text fields"""
        if not search:
            return query

        text_fields = [f.name for f in fields if f.type in ["string", "text"]]
        if not text_fields:
            return query

        conditions = []
        for field_name in text_fields:
            if hasattr(model, field_name):
                conditions.append(getattr(model, field_name).like(f"%{search}%"))

        if conditions:
            query = query.filter(or_(*conditions))

        return query

    @staticmethod
    def apply_sorting(query, model: Type, ordering: str):
        """Apply sorting to query"""
        if not ordering:
            return query

        order_fields = ordering.split(",")
        for field in order_fields:
            if field.startswith("-"):
                field_name = field[1:]
                if hasattr(model, field_name):
                    query = query.order_by(desc(getattr(model, field_name)))
            else:
                if hasattr(model, field):
                    query = query.order_by(asc(getattr(model, field)))

        return query

    @staticmethod
    def to_csv(data: List[Dict[str, Any]], fields: List[FieldMetadata]) -> str:
        """Convert data to CSV format"""
        if not data:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[f.name for f in fields])
        writer.writeheader()

        for row in data:
            csv_row = {}
            for field in fields:
                value = row.get(field.name)
                if value is None:
                    csv_row[field.name] = ""
                elif isinstance(value, datetime):
                    csv_row[field.name] = value.isoformat()
                else:
                    csv_row[field.name] = str(value)
            writer.writerow(csv_row)

        return output.getvalue()

    @classmethod
    def create_router(
        cls,
        model: Type,
        name: str,
        prefix: str = "",
        tags: Optional[List[str]] = None
    ) -> APIRouter:
        """Create a complete CRUD router for a model"""
        router = APIRouter(prefix=prefix, tags=tags or [name])
        fields = cls.get_model_fields(model)
        primary_key = next((f.name for f in fields if f.readonly and f.name in ["id", "ID", f"{model.__tablename__}_id"]), "id")

        @router.get("/meta")
        async def get_metadata():
            """Get model metadata for dynamic rendering"""
            return {
                "status": "success",
                "data": {
                    "name": name,
                    "tableName": model.__tablename__,
                    "fields": [f.dict() for f in fields]
                }
            }

        @router.get("/")
        async def list_records(
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=200),
            ordering: Optional[str] = Query(None),
            search: Optional[str] = Query(None),
            format: str = Query("json", regex="^(json|csv)$"),
            db: Session = Depends(get_db),
            **filters
        ):
            """List all records with pagination, filtering, search, and sorting"""
            try:
                query = db.query(model)

                # Apply filters
                query = cls.apply_filters(query, model, filters)

                # Apply search
                query = cls.apply_search(query, model, search, fields)

                # Apply sorting
                query = cls.apply_sorting(query, model, ordering)

                # Get total count
                total = query.count()

                # Apply pagination
                offset = (page - 1) * page_size
                records = query.offset(offset).limit(page_size).all()

                # Convert to dict
                data = []
                for record in records:
                    record_dict = {}
                    for field in fields:
                        value = getattr(record, field.name, None)
                        if isinstance(value, datetime):
                            record_dict[field.name] = value.isoformat()
                        else:
                            record_dict[field.name] = value
                    data.append(record_dict)

                # CSV export
                if format == "csv":
                    csv_data = cls.to_csv(data, fields)
                    return Response(
                        content=csv_data,
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename={model.__tablename__}.csv"
                        }
                    )

                return {
                    "status": "success",
                    "data": data,
                    "meta": {
                        "page": page,
                        "page_size": page_size,
                        "total": total
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail={
                    "status": "error",
                    "error": {
                        "code": "SERVER_ERROR",
                        "message": str(e)
                    }
                })

        @router.get("/{record_id}")
        async def get_record(
            record_id: int,
            db: Session = Depends(get_db)
        ):
            """Get a single record by ID"""
            try:
                record = db.query(model).filter(
                    getattr(model, primary_key) == record_id
                ).first()

                if not record:
                    raise HTTPException(status_code=404, detail={
                        "status": "error",
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"{name} not found"
                        }
                    })

                record_dict = {}
                for field in fields:
                    value = getattr(record, field.name, None)
                    if isinstance(value, datetime):
                        record_dict[field.name] = value.isoformat()
                    else:
                        record_dict[field.name] = value

                return {
                    "status": "success",
                    "data": record_dict
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail={
                    "status": "error",
                    "error": {
                        "code": "SERVER_ERROR",
                        "message": str(e)
                    }
                })

        return router
