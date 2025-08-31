from typing import List
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import ProductIn, ProductOut, ProductUpdate, ProductUpdateOut
from store.core.exceptions import NotFoundException
from datetime import datetime


class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        product_model = ProductModel(**body.model_dump())
        await self.collection.insert_one(product_model.model_dump())

        return ProductOut(**product_model.model_dump())

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, min_price: float | None = None, max_price: float | None = None) -> List[ProductOut]:
        filtro = {}
        if min_price is not None and max_price is not None:
            filtro["price"] = {"$gt": min_price, "$lt": max_price}

        cursor = self.collection.find(filtro)
        produtos = await cursor.to_list(length=100)
        return [ProductOut.model_validate(prod) for prod in produtos]
    


    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        data = body.model_dump(exclude_unset=True)
        data["updated at"] = datetime.utcnow()
        result = await self.collection.update_one({"id": id}, {"$set": data})

        if result.matched_count == 0:
            raise NotFoundException("Produto não encontrado para atualização")
        
        updated = await self.collection.find_one({"id": id})

        return ProductUpdateOut(**updated)

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()