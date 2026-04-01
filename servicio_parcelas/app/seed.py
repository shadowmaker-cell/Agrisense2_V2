from app.database import SessionLocal
from app.models.parcela import TipoCultivo

TIPOS_CULTIVO = [
    { "nombre": "Maiz",        "descripcion": "Cultivo de maiz amarillo y blanco",           "temporada": "todo_anio" },
    { "nombre": "Arroz",       "descripcion": "Cultivo de arroz de secano e irrigado",        "temporada": "todo_anio" },
    { "nombre": "Cafe",        "descripcion": "Cafe arabica y robusto",                       "temporada": "todo_anio" },
    { "nombre": "Platano",     "descripcion": "Platano harton y dominico",                    "temporada": "todo_anio" },
    { "nombre": "Yuca",        "descripcion": "Yuca amarga y dulce",                          "temporada": "todo_anio" },
    { "nombre": "Papa",        "descripcion": "Papa pastusa, criolla y r12",                  "temporada": "todo_anio" },
    { "nombre": "Tomate",      "descripcion": "Tomate chonto y larga vida",                   "temporada": "todo_anio" },
    { "nombre": "Cana",        "descripcion": "Cana de azucar para panela y azucar",          "temporada": "todo_anio" },
    { "nombre": "Cacao",       "descripcion": "Cacao fino de aroma",                          "temporada": "todo_anio" },
    { "nombre": "Aguacate",    "descripcion": "Aguacate hass y papelillo",                    "temporada": "todo_anio" },
    { "nombre": "Frijol",      "descripcion": "Frijol voluble y arbustivo",                   "temporada": "verano"    },
    { "nombre": "Soya",        "descripcion": "Soya para aceite y proteina",                  "temporada": "verano"    },
    { "nombre": "Sorgo",       "descripcion": "Sorgo para forraje y grano",                   "temporada": "verano"    },
    { "nombre": "Palma",       "descripcion": "Palma africana para aceite",                   "temporada": "todo_anio" },
    { "nombre": "Flores",      "descripcion": "Rosas, claveles y crisantemos para exportacion","temporada": "todo_anio" },
]


def seed():
    db = SessionLocal()
    try:
        existentes = db.query(TipoCultivo).count()
        if existentes > 0:
            print(f"Seed ya aplicado — {existentes} tipos de cultivo existentes")
            return

        for t in TIPOS_CULTIVO:
            db.add(TipoCultivo(**t))
        db.commit()
        print(f"✓ {len(TIPOS_CULTIVO)} tipos de cultivo insertados")
    except Exception as e:
        print(f"Error en seed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()