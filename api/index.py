import cv2
import numpy as np
import base64
import json, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
from mangum import Mangum

app = FastAPI(title="SkinTone ID API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SkinAnalysisRequest(BaseModel):
    image_base64: str

class SkinAnalysisResponse(BaseModel):
    hex_code: str
    rgb_values: Dict[str, int]
    fitzpatrick_score: int
    tone_name: str
    undertone: str
    recommendations: List[str]
    palette: Dict[str, str]
    unflattering: Dict[str, str]

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}".upper()

def analyze_undertone(r: int, g: int, b: int) -> str:
    if r > g + 10 and r > b + 10:
        return "Cálido"
    elif b > r + 10 or (g > r and g > b):
        return "Frío"
    else:
        return "Neutro"

def classify_fitzpatrick(r: int, g: int, b: int) -> int:
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    if luminance > 200:
        return 1
    elif luminance > 180:
        return 2
    elif luminance > 160:
        return 3
    elif luminance > 140:
        return 4
    elif luminance > 100:
        return 5
    else:
        return 6

def fitzpatrick_to_tone_name(fitzpatrick: int) -> str:
    tone_names = {1: "Blanco", 2: "Claro", 3: "Trigueño Claro", 4: "Trigueño", 5: "Moreno", 6: "Negro"}
    return tone_names.get(fitzpatrick, "Indefinido")

def generate_recommendations(fitzpatrick: int, undertone: str) -> List[str]:
    recommendations = []
    if fitzpatrick in [1, 2]:
        recommendations.append("Protector solar SPF 50+ es esencial diariamente")
        recommendations.append("Evita exposición solar prolongada")
        recommendations.append("Hidratación intensiva recomendada")
    elif fitzpatrick in [3, 4]:
        recommendations.append("Protector solar SPF 30+ recomendado")
        recommendations.append("Tolera bien la exposición solar moderada")
        recommendations.append("Mantén rutina de hidratación regular")
    else:
        recommendations.append("Protector solar SPF 15-30 como medida preventiva")
        recommendations.append("Menor riesgo de quemaduras solares")
        recommendations.append("Enfócate en antienvejecimiento y luminosidad")
    if undertone == "Cálido":
        recommendations.append("Los tonos dorados y cálidos favorecen tu piel")
        recommendations.append("Evita colores muy fríos o plateados")
    elif undertone == "Frío":
        recommendations.append("Los tonos plateados y fríos son tu mejor aliado")
        recommendations.append("Colores azulados y rosáceos te favorecen")
    else:
        recommendations.append("Tienes versatilidad: dorados y plateados te sientan bien")
        recommendations.append("Puedes usar ambos tonos metálicos sin problema")
    return recommendations

def analyze_color_palette(hex_color: str, fitzpatrick: int) -> Dict[str, str]:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    comp_r, comp_g, comp_b = 255 - r, 255 - g, 255 - b
    ana_r = min(255, r + 30) if r < 225 else r - 30
    ana_g = min(255, g + 30) if g < 225 else g - 30
    ana_b = min(255, b + 30) if b < 225 else b - 30
    return {
        "primary": hex_color,
        "complementary": rgb_to_hex(comp_r, comp_g, comp_b),
        "analogous": rgb_to_hex(ana_r, ana_g, ana_b),
        "highlight": rgb_to_hex(min(255, r + 50), min(255, g + 50), min(255, b + 50))
    }

def generate_unflattering_colors(hex_color: str, undertone: str) -> Dict[str, str]:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    if undertone == "Cálido":
        unflattering_primary = rgb_to_hex(max(0, r - 60), max(0, g - 40), min(255, b + 80))
        unflattering_secondary = rgb_to_hex(min(255, r + 30), min(255, g + 30), max(0, b - 50))
        avoid_note = "Evita plateados y tonos azulados fríos"
    elif undertone == "Frío":
        unflattering_primary = rgb_to_hex(min(255, r + 70), min(255, g + 40), max(0, b - 30))
        unflattering_secondary = rgb_to_hex(min(255, r + 40), min(255, g + 60), min(255, b + 40))
        avoid_note = "Evita tonos dorados y naranjas cálidos"
    else:
        unflattering_primary = rgb_to_hex(min(255, r + 50), min(255, g + 50), min(255, b + 50))
        unflattering_secondary = rgb_to_hex(max(0, r - 40), max(0, g - 40), max(0, b - 40))
        avoid_note = "Evita extremos muy cálidos o muy fríos"
    return {
        "unflattering_primary": unflattering_primary,
        "unflattering_secondary": unflattering_secondary,
        "muddy_tone": rgb_to_hex(max(0, r - 30), max(0, g - 30), max(0, b - 30)),
        "avoid_note": avoid_note
    }

class FaceDetector:
    def __init__(self):
        self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("No se pudo cargar el clasificador Haar Cascade")

    def process_image(self, image_base64: str) -> Dict:
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        image_data = base64.b64decode(image_base64)
        image_array = np.frombuffer(image_data, dtype=np.uint8)
        image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("No se pudo decodificar la imagen JPEG desde Base64")

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        mean_luminance = cv2.mean(gray)[0]
        if mean_luminance < 30 or mean_luminance > 220:
            raise ValueError("Iluminación inadecuada: imagen demasiado oscura o sobreexpuesta")

        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100), flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(faces) == 0:
            raise ValueError("No se detectó un rostro válido en la imagen")

        x, y, w, h = faces[0]
        cheek_x = x + int(w * 0.35)
        cheek_y = y + int(h * 0.60)
        roi_size = 30
        roi_x1 = max(0, cheek_x - roi_size // 2)
        roi_y1 = max(0, cheek_y - roi_size // 2)
        roi_x2 = min(image_bgr.shape[1], roi_x1 + roi_size)
        roi_y2 = min(image_bgr.shape[0], roi_y1 + roi_size)
        roi = image_bgr[roi_y1:roi_y2, roi_x1:roi_x2]

        mean_color = cv2.mean(roi)
        b, g, r = int(mean_color[0]), int(mean_color[1]), int(mean_color[2])
        return {"r": r, "g": g, "b": b}

face_detector = FaceDetector()

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "SkinTone ID Backend is running", "version": "1.0.0"}

@app.post("/analyze", response_model=SkinAnalysisResponse)
async def analyze_skin(request: SkinAnalysisRequest):
    try:
        if not request.image_base64 or len(request.image_base64) < 100:
            raise ValueError("Imagen Base64 inválida o muy pequeña")

        color_result = face_detector.process_image(request.image_base64)
        r, g, b = color_result["r"], color_result["g"], color_result["b"]
        hex_code = rgb_to_hex(r, g, b)
        fitzpatrick = classify_fitzpatrick(r, g, b)
        undertone = analyze_undertone(r, g, b)
        recommendations = generate_recommendations(fitzpatrick, undertone)
        palette = analyze_color_palette(hex_code, fitzpatrick)
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
        raise HTTPException(status_code=400, detail=f"Error en validación de imagen: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en el servidor: {str(e)}")

@app.get("/")
async def root():
    return {"name": "SkinTone ID API", "version": "1.0.0", "endpoints": {"health": "/health (GET)", "analyze": "/analyze (POST)"}}

handler = Mangum(app)
