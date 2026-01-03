"""Auto-generated CRUD endpoints for all models - MINIMAL"""
from fastapi import APIRouter
from core.base import Base
from typing import List, Tuple, Type

def get_models_list():
    """Get list of all models with their endpoints"""
    models = []
    for mapper in Base.registry.mappers:
        model_class = mapper.class_
        table_name = mapper.class_.__tablename__
        models.append({
            "name": table_name.replace("_", " ").title(),
            "tableName": table_name
        })
    return models