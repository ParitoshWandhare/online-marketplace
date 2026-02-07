"""
APIRouter for vision AI. Routes are thin: they only parse the request (UploadFile)
and forward to the service layer in `vision_ai.services.vision_service`.

FIXED: Added both underscore and hyphenated route versions for compatibility
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


# Story Generation (both underscore and hyphen versions)
@router.post("/generate_story")
@router.post("/generate-story")
async def route_generate_story(image: UploadFile = File(...)) -> Any:
    """Generate a story from the provided image."""
    try:
        return await generate_story(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Similar Crafts (both versions)
@router.post("/similar_crafts")
@router.post("/similar-crafts")
async def route_similar_crafts(image: UploadFile = File(...)) -> Any:
    try:
        return await similar_crafts(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Price Suggestion (both versions)
@router.post("/price_suggestion")
@router.post("/price-suggestion")
async def route_price_suggestion(image: UploadFile = File(...)) -> Any:
    try:
        return await price_suggestion(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Complementary Products (both versions)
@router.post("/complementary_products")
@router.post("/complementary-products")
async def route_complementary_products(image: UploadFile = File(...)) -> Any:
    try:
        return await complementary_products(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Purchase Analysis (both versions)
@router.post("/purchase_analysis")
@router.post("/purchase-analysis")
async def route_purchase_analysis(image: UploadFile = File(...)) -> Any:
    try:
        return await purchase_analysis(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Fraud Detection (both versions)
@router.post("/fraud_detection")
@router.post("/fraud-detection")
async def route_fraud_detection(image: UploadFile = File(...)) -> Any:
    try:
        return await fraud_detection(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Order Fulfillment (both versions)
@router.post("/order_fulfillment_analysis")
@router.post("/order-fulfillment-analysis")
async def route_order_fulfillment_analysis(image: UploadFile = File(...)) -> Any:
    try:
        return await order_fulfillment_analysis(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Quality Predictions (both versions)
@router.post("/quality_predictions")
@router.post("/quality-predictions")
async def route_quality_predictions(image: UploadFile = File(...)) -> Any:
    try:
        return await quality_predictions(image)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))