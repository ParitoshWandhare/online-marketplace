"""
APIRouter for vision AI. Routes are thin: they only parse the request (UploadFile)
and forward to the service layer in `vision_ai.services.vision_service`.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Any


# Import service functions
from ...vision_ai.services.vision_service import (
    generate_story,
    similar_crafts,
    price_suggestion,
    complementary_products,
    purchase_analysis,
    fraud_detection,
    order_fulfillment_analysis,
    quality_predictions,
)


router = APIRouter()


@router.post("/generate_story")
async def route_generate_story(image: UploadFile = File(...)) -> Any:
    """Generate a story from the provided image."""
    try:
        return await generate_story(image)
    except HTTPException:
        raise
    except Exception as e:
        # Convert unknown errors into a 500 HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/similar_crafts")
async def route_similar_crafts(image: UploadFile = File(...)) -> Any:
    try:
        return await similar_crafts(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price_suggestion")
async def route_price_suggestion(image: UploadFile = File(...)) -> Any:
    try:
        return await price_suggestion(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complementary_products")
async def route_complementary_products(image: UploadFile = File(...)) -> Any:
    try:
        return await complementary_products(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase_analysis")
async def route_purchase_analysis(image: UploadFile = File(...)) -> Any:
    try:
        return await purchase_analysis(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fraud_detection")
async def route_fraud_detection(image: UploadFile = File(...)) -> Any:
    try:
        return await fraud_detection(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order_fulfillment_analysis")
async def route_order_fulfillment_analysis(image: UploadFile = File(...)) -> Any:
    try:
        return await order_fulfillment_analysis(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality_predictions")
async def route_quality_predictions(image: UploadFile = File(...)) -> Any:
    try:
        return await quality_predictions(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))