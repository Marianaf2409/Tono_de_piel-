"""
Backend FastAPI para SkinTone ID.
Orquesta la recepción de imágenes, procesamiento y respuesta de análisis de piel.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
import os

from .services.image_service import face_detector
from .utils.color_math import (
    rgb_to_hex,
    classify_fitzpatrick,
    analyze_undertone,
    generate_recommendations,
    analyze_color_palette,
    generate_unflattering_colors,
    fitzpatrick_to_tone_name
)

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ============================================================================
# MODELOS PYDANTIC (Validación de datos)
# ============================================================================

class SkinAnalysisRequest(BaseModel):
    """Modelo de validación para la solicitud de análisis de piel."""
    image_base64: str


class SkinAnalysisResponse(BaseModel):
    """Modelo de respuesta del análisis de piel."""
    hex_code: str
    rgb_values: Dict[str, int]
    fitzpatrick_score: int
    tone_name: str
    undertone: str
    recommendations: List[str]
    palette: Dict[str, str]
    unflattering: Dict[str, str]


# ============================================================================
# INICIALIZACIÓN DE FASTAPI
# ============================================================================

app = FastAPI(
    title="SkinTone ID API",
    description="Sistema Inteligente de Detección y Análisis de Fototipo Cutáneo",
    version="1.0.0"
)

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")


@app.get("/api")
async def api_root():
    return {
        "name": "SkinTone ID API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health (GET)",
            "analyze": "/api/analyze (POST)"
        }
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "SkinTone ID Backend is running",
        "version": "1.0.0"
    }


@app.post("/api/analyze", response_model=SkinAnalysisResponse)
async def analyze_skin(request: SkinAnalysisRequest):
    """
    Endpoint principal de análisis de piel.
    
    Recibe una imagen en formato Base64, detecta el rostro, extrae la región
    de las mejillas, analiza el color y retorna el fototipo Fitzpatrick,
    subtóno y recomendaciones.
    
    Args:
        request: SkinAnalysisRequest con image_base64
        
    Returns:
        SkinAnalysisResponse con todos los datos del análisis
        
    Raises:
        HTTPException 400: Si hay errores en la imagen o detección
    """
    try:
        # Validar que la imagen Base64 no esté vacía
        if not request.image_base64 or len(request.image_base64) < 100:
            raise ValueError("Imagen Base64 inválida o muy pequeña")
        
        # Procesar imagen: detectar rostro y extraer color
        color_result = face_detector.process_image(request.image_base64)
        
        r = color_result["r"]
        g = color_result["g"]
        b = color_result["b"]
        
        # Convertir a HEX
        hex_code = rgb_to_hex(r, g, b)
        
        # Clasificar en escala Fitzpatrick
        fitzpatrick = classify_fitzpatrick(r, g, b)
        
        # Analizar subtóno
        undertone = analyze_undertone(r, g, b)
        
        # Generar recomendaciones
        recommendations = generate_recommendations(fitzpatrick, undertone)
        
        # Generar paleta de colores
        palette = analyze_color_palette(hex_code, fitzpatrick)
        
        # Retornar respuesta validada
        # Generar paleta de colores recomendada
        palette = analyze_color_palette(hex_code, fitzpatrick)
        
        # Generar paleta de colores NO favorecedores
        unflattering = generate_unflattering_colors(hex_code, undertone)
        
        return SkinAnalysisResponse(
            hex_code=hex_code,
            rgb_values={"r": r, "g": g, "b": b},
            fitzpatrick_score=fitzpatrick,
            tone_name=fitzpatrick_to_tone_name(fitzpatrick),
            undertone=undertone,
            recommendations=recommendations,
            palette=palette,
            unflattering=unflattering
        )
    
    except ValueError as e:
        # Error en validación de imagen o procesamiento
        raise HTTPException(
            status_code=400,
            detail=f"Error en validación de imagen: {str(e)}"
        )
    
    except Exception as e:
        # Error interno
        raise HTTPException(
            status_code=500,
            detail=f"Error interno en el servidor: {str(e)}"
        )


@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_dir, "index.html"))


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Configurar y ejecutar servidor
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
