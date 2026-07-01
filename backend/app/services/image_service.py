"""
Módulo de Visión Artificial.
Detección de rostros, extracción de ROI y validación de iluminación.
"""

import cv2
import numpy as np
import base64
from typing import Tuple, Dict


class FaceDetector:
    """Clase para detectar rostros y extraer regiones de interés (ROI)."""
    
    def __init__(self):
        """Inicializa el clasificador Haar Cascade para detectar rostros."""
        try:
            self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
            
            if self.face_cascade.empty():
                raise RuntimeError("No se pudo cargar el clasificador Haar Cascade")
        except Exception as e:
            print(f"Error inicializando detector: {e}")
            self.face_cascade = None
    
    def _decode_base64_image(self, image_base64: str) -> np.ndarray:
        """
        Decodifica una imagen en formato Base64 a array de NumPy.
        
        Args:
            image_base64: Cadena Base64 de la imagen (sin prefijo 'data:image/...')
            
        Returns:
            Array de NumPy con la imagen en formato BGR
            
        Raises:
            ValueError: Si el Base64 es inválido
        """
        try:
            # Eliminar prefijo si existe
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            
            # Decodificar Base64
            image_data = base64.b64decode(image_base64)
            image_array = np.frombuffer(image_data, dtype=np.uint8)
            image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image_bgr is None:
                raise ValueError("No se pudo decodificar la imagen JPEG desde Base64")
            
            return image_bgr
        except Exception as e:
            raise ValueError(f"Error al decodificar imagen Base64: {str(e)}")
    
    def _validate_luminance(self, image: np.ndarray, threshold_dark: float = 30, threshold_bright: float = 220) -> bool:
        """
        Valida que la imagen tenga iluminación adecuada.
        
        Args:
            image: Array de imagen BGR
            threshold_dark: Umbral mínimo de luminancia promedio
            threshold_bright: Umbral máximo de luminancia promedio
            
        Returns:
            True si la iluminación es válida, False si es demasiado oscura o quemada
        """
        # Convertir BGR a escala de grises (luminancia)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calcular promedio de luminancia
        mean_luminance = cv2.mean(gray)[0]
        
        # Validar rango
        if mean_luminance < threshold_dark or mean_luminance > threshold_bright:
            return False
        
        return True
    
    def detect_face(self, image_base64: str) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Detecta un rostro en la imagen y retorna la imagen y el rectángulo del rostro.
        
        Args:
            image_base64: Cadena Base64 de la imagen
            
        Returns:
            Tupla (imagen BGR, (x, y, ancho, alto)) del rostro detectado
            
        Raises:
            ValueError: Si no se detecta un rostro o la iluminación es inválida
        """
        # Decodificar imagen
        image = self._decode_base64_image(image_base64)
        
        # Validar que el clasificador está disponible
        if self.face_cascade is None:
            raise ValueError("Detector de rostros no disponible. Instale opencv-python-headless si usa servidor sin GUI.")
        
        # Validar iluminación
        if not self._validate_luminance(image):
            raise ValueError("Iluminación inadecuada: imagen demasiado oscura o sobreexpuesta")
        
        # Convertir a escala de grises para detección
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detectar rostros
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Validar que se detectó al menos un rostro
        if len(faces) == 0:
            raise ValueError("No se detectó un rostro válido en la imagen")
        
        # Tomar el rostro más grande (primer elemento está ordenado por tamaño)
        x, y, w, h = faces[0]
        
        return image, (x, y, w, h)
    
    def extract_roi(self, image: np.ndarray, face: Tuple[int, int, int, int], roi_size: int = 30) -> np.ndarray:
        """
        Extrae la Región de Interés (ROI) de 30x30 píxeles de la zona de las mejillas.
        
        Args:
            image: Array de imagen BGR
            face: Tupla (x, y, ancho, alto) del rostro
            roi_size: Tamaño del ROI en píxeles (default 30x30)
            
        Returns:
            Array de la región extraída
        """
        x, y, w, h = face
        
        # Calcular el centro de la mejilla derecha (aproximadamente)
        # Tomamos un punto en el tercio inferior del rostro hacia el lado derecho
        cheek_x = x + int(w * 0.35)  # Desplazamiento horizontal
        cheek_y = y + int(h * 0.60)  # Desplazamiento vertical (parte media-baja)
        
        # Asegurar que el ROI esté dentro de los límites de la imagen
        roi_x1 = max(0, cheek_x - roi_size // 2)
        roi_y1 = max(0, cheek_y - roi_size // 2)
        roi_x2 = min(image.shape[1], roi_x1 + roi_size)
        roi_y2 = min(image.shape[0], roi_y1 + roi_size)
        
        # Extraer ROI
        roi = image[roi_y1:roi_y2, roi_x1:roi_x2]
        
        return roi
    
    def extract_color_from_roi(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """
        Extrae el color promedio de la región de interés.
        
        Args:
            roi: Array de imagen BGR de la región
            
        Returns:
            Tupla (B, G, R) promediada - NOTA: OpenCV usa BGR, convertimos a RGB
        """
        # Calcular valores promedio de cada canal
        mean_color = cv2.mean(roi)
        
        # mean_color es (B, G, R, alfa) en BGR
        # Convertir a RGB para retornar
        b, g, r = int(mean_color[0]), int(mean_color[1]), int(mean_color[2])
        
        return r, g, b  # Retornamos en formato RGB
    
    def process_image(self, image_base64: str) -> Dict:
        """
        Proceso completo: detectar rostro, extraer ROI y obtener color.
        
        Args:
            image_base64: Cadena Base64 de la imagen
            
        Returns:
            Diccionario con resultado: {"r": int, "g": int, "b": int}
            
        Raises:
            ValueError: Si ocurre algún error en el procesamiento
        """
        try:
            # Detectar rostro
            image, face = self.detect_face(image_base64)
            
            # Extraer ROI
            roi = self.extract_roi(image, face)
            
            # Extraer color promedio
            r, g, b = self.extract_color_from_roi(roi)
            
            return {"r": r, "g": g, "b": b}
        
        except Exception as e:
            raise ValueError(f"Error en procesamiento de imagen: {str(e)}")


# Instancia global del detector
face_detector = FaceDetector()
