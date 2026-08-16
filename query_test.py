import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
from app.db.database import SessionLocal
from app.models.models import Ejercicio, ExerciseOwnership
from sqlalchemy import or_

db = SessionLocal()
base_query = db.query(Ejercicio)
official_total = base_query.filter(~Ejercicio.ownership.has()).count()

print("Official total:", official_total)

visibility = or_(~Ejercicio.ownership.has())
q2 = base_query.filter(visibility).filter(~Ejercicio.ownership.has())
print("Visible official total:", q2.count())

