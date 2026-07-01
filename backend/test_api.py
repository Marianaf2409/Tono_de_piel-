#!/usr/bin/env python3
"""
Script de prueba rápida del API SkinTone ID
Para verificar que el backend está funcionando correctamente
"""

import requests
import base64
import sys
from pathlib import Path

API_URL = "http://127.0.0.1:8000"

def test_health():
    """Prueba el endpoint de salud"""
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ Health Check: OK")
            print(f"   {response.json()}")
            return True
        else:
            print(f"❌ Health Check: Error {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al backend")
        print(f"   ¿El servidor está corriendo en {API_URL}?")
        return False

def create_test_image():
    """Crea una imagen PNG de prueba"""
    try:
        from PIL import Image
        import numpy as np
        import tempfile
        
        # Crear imagen simple de color piel (tonalidad media)
        img = Image.new('RGB', (300, 300), color=(220, 170, 150))
        
        # Guardar temporalmente en directorio válido para Windows
        test_image_path = Path(tempfile.gettempdir()) / 'test_skin.jpg'
        img.save(test_image_path, format='JPEG')
        
        return test_image_path
    except ImportError:
        print("⚠️  Pillow no está instalada. Saltando prueba de imagen.")
        return None

def encode_image_to_base64(image_path):
    """Codifica una imagen a Base64"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')

def test_analysis(image_base64):
    """Prueba el endpoint de análisis"""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"image_base64": image_base64},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Analysis Endpoint: OK")
            data = response.json()
            print(f"   HEX: {data['hex_code']}")
            print(f"   RGB: r={data['rgb_values']['r']}, g={data['rgb_values']['g']}, b={data['rgb_values']['b']}")
            print(f"   Fitzpatrick: {data['fitzpatrick_score']}/6")
            print(f"   Undertone: {data['undertone']}")
            return True
        else:
            print(f"❌ Analysis Error {response.status_code}")
            print(f"   {response.json()}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: El servidor tardó demasiado en responder")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("\n" + "="*50)
    print("  SkinTone ID - Test API Backend")
    print("="*50 + "\n")
    
    # Prueba 1: Health Check
    print("1. Probando endpoint de salud...")
    if not test_health():
        sys.exit(1)
    
    print("\n2. Probando endpoint de análisis...")
    
    # Intentar crear imagen de prueba
    image_path = create_test_image()
    
    if image_path and image_path.exists():
        print(f"   Imagen de prueba creada: {image_path}")
        
        # Codificar a Base64
        image_base64 = encode_image_to_base64(image_path)
        print(f"   Base64: {len(image_base64)} caracteres")
        
        # Prueba análisis
        if not test_analysis(image_base64):
            sys.exit(1)
    else:
        print("⚠️  No se pudo crear imagen de prueba (Pillow no instalada)")
        print("   Para instalar: pip install Pillow")
    
    print("\n" + "="*50)
    print("  ✅ Todas las pruebas pasaron correctamente")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
