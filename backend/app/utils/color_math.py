"""
Módulo de matemática de colores y clasificación Fitzpatrick.
Realiza conversiones RGB/HEX, análisis de subtóno y mapeo a la escala dermatológica.
"""

import numpy as np
from typing import Dict, Tuple, List


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convierte valores RGB a formato HEX.
    
    Args:
        r: Valor rojo (0-255)
        g: Valor verde (0-255)
        b: Valor azul (0-255)
        
    Returns:
        Cadena en formato HEX (#RRGGBB)
    """
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convierte formato HEX a RGB.
    
    Args:
        hex_color: Cadena en formato HEX (#RRGGBB)
        
    Returns:
        Tupla (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def analyze_undertone(r: int, g: int, b: int) -> str:
    """
    Analiza el subtóno del color de piel basado en los canales RGB.
    
    Args:
        r: Valor rojo
        g: Valor verde
        b: Valor azul
        
    Returns:
        "Cálido" si predomina rojo/amarillo
        "Frío" si predomina azul
        "Neutro" si están balanceados
    """
    if r > g + 10 and r > b + 10:
        return "Cálido"
    elif b > r + 10 or (g > r and g > b):
        return "Frío"
    else:
        return "Neutro"


def classify_fitzpatrick(r: int, g: int, b: int) -> int:
    """
    Clasifica el tono de piel en la escala Fitzpatrick (I-VI).
    
    Algoritmo basado en la luminancia y saturación del color:
    - I (muy pálido): Luminancia > 200
    - II (pálido): Luminancia 180-200
    - III (claro): Luminance 160-180
    - IV (moreno): Luminance 140-160
    - V (oscuro): Luminance 100-140
    - VI (muy oscuro): Luminance < 100
    
    Args:
        r: Valor rojo
        g: Valor verde
        b: Valor azul
        
    Returns:
        Entero de 1 a 6 representando el fototipo Fitzpatrick
    """
    # Calcular luminancia usando fórmula estándar (ITU-R BT.601)
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
    """
    Convierte el número de fototipo Fitzpatrick a nombre de tono humano moderno.
    
    Args:
        fitzpatrick: Número de fototipo (1-6)
        
    Returns:
        Nombre del tono de piel en español (simple y directo)
    """
    tone_names = {
        1: "Blanco",
        2: "Claro",
        3: "Trigueño Claro",
        4: "Trigueño",
        5: "Moreno",
        6: "Negro"
    }
    return tone_names.get(fitzpatrick, "Indefinido")


def generate_recommendations(fitzpatrick: int, undertone: str) -> List[str]:
    """
    Genera recomendaciones de cuidado y colorimetría basadas en el fototipo.
    
    Args:
        fitzpatrick: Número de fototipo (1-6)
        undertone: Tipo de subtóno ("Cálido", "Frío", "Neutro")
        
    Returns:
        Lista de recomendaciones personalizadas
    """
    recommendations = []
    
    # Recomendaciones por fototipo
    if fitzpatrick in [1, 2]:
        recommendations.append("Protector solar SPF 50+ es esencial diariamente")
        recommendations.append("Evita exposición solar prolongada")
        recommendations.append("Hidratación intensiva recomendada")
    elif fitzpatrick in [3, 4]:
        recommendations.append("Protector solar SPF 30+ recomendado")
        recommendations.append("Tolera bien la exposición solar moderada")
        recommendations.append("Mantén rutina de hidratación regular")
    else:  # fitzpatrick in [5, 6]
        recommendations.append("Protector solar SPF 15-30 como medida preventiva")
        recommendations.append("Menor riesgo de quemaduras solares")
        recommendations.append("Enfócate en antienvejecimiento y luminosidad")
    
    # Recomendaciones por subtóno
    if undertone == "Cálido":
        recommendations.append("Los tonos dorados y cálidos favorecen tu piel")
        recommendations.append("Evita colores muy fríos o plateados")
    elif undertone == "Frío":
        recommendations.append("Los tonos plateados y fríos son tu mejor aliado")
        recommendations.append("Colores azulados y rosáceos te favorecen")
    else:  # Neutro
        recommendations.append("Tienes versatilidad: dorados y plateados te sientan bien")
        recommendations.append("Puedes usar ambos tonos metálicos sin problema")
    
    return recommendations


def analyze_color_palette(hex_color: str, fitzpatrick: int) -> Dict[str, str]:
    """
    Genera una paleta de colores complementarios y sugeridos.
    
    Args:
        hex_color: Color base en formato HEX
        fitzpatrick: Número de fototipo
        
    Returns:
        Diccionario con paleta de colores sugeridos
    """
    r, g, b = hex_to_rgb(hex_color)
    
    # Complementario (invertir en HSV conceptualmente, aquí simplificado)
    comp_r = 255 - r
    comp_g = 255 - g
    comp_b = 255 - b
    
    # Análogo (rotación de tono)
    ana_r = min(255, r + 30) if r < 225 else r - 30
    ana_g = min(255, g + 30) if g < 225 else g - 30
    ana_b = min(255, b + 30) if b < 225 else b - 30
    
    palette = {
        "primary": hex_color,
        "complementary": rgb_to_hex(comp_r, comp_g, comp_b),
        "analogous": rgb_to_hex(ana_r, ana_g, ana_b),
        "highlight": rgb_to_hex(
            min(255, r + 50),
            min(255, g + 50),
            min(255, b + 50)
        )
    }
    
    return palette


def generate_unflattering_colors(hex_color: str, undertone: str) -> Dict[str, str]:
    """
    Genera colores que NO favorecen según el subtóno.
    
    Args:
        hex_color: Color base en formato HEX
        undertone: Subtóno ("Cáldo", "Frío", "Neutro")
        
    Returns:
        Diccionario con colores a evitar y nota explicativa
    """
    r, g, b = hex_to_rgb(hex_color)
    
    if undertone == "Cálido":
        unflattering_primary = rgb_to_hex(
            max(0, r - 60), max(0, g - 40), min(255, b + 80)
        )
        unflattering_secondary = rgb_to_hex(
            min(255, r + 30), min(255, g + 30), max(0, b - 50)
        )
        avoid_note = "Evita plateados y tonos azulados fríos"
    elif undertone == "Frío":
        unflattering_primary = rgb_to_hex(
            min(255, r + 70), min(255, g + 40), max(0, b - 30)
        )
        unflattering_secondary = rgb_to_hex(
            min(255, r + 40), min(255, g + 60), min(255, b + 40)
        )
        avoid_note = "Evita tonos dorados y naranjas cálidos"
    else:
        unflattering_primary = rgb_to_hex(
            min(255, r + 50), min(255, g + 50), min(255, b + 50)
        )
        unflattering_secondary = rgb_to_hex(
            max(0, r - 40), max(0, g - 40), max(0, b - 40)
        )
        avoid_note = "Evita extremos muy cálidos o muy fríos"
    
    return {
        "unflattering_primary": unflattering_primary,
        "unflattering_secondary": unflattering_secondary,
        "muddy_tone": rgb_to_hex(
            max(0, r - 30), max(0, g - 30), max(0, b - 30)
        ),
        "avoid_note": avoid_note
    }
