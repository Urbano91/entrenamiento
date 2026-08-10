import getpass
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.models import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def main():
    db = SessionLocal()
    try:
        username = input("Usuario: ").strip()
        
        user_exists = db.query(Usuario).filter(Usuario.usuario == username).first()
        if user_exists:
            print("El usuario ya existe.")
            return

        password = getpass.getpass("Contraseña: ")
        confirm_password = getpass.getpass("Confirmar contraseña: ")

        if password != confirm_password:
            print("Las contraseñas no coinciden.")
            return
            
        hashed_password = get_password_hash(password)
        
        nuevo_usuario = Usuario(usuario=username, password_hash=hashed_password, activo=True)
        db.add(nuevo_usuario)
        db.commit()
        
        print("Usuario creado correctamente.")
    except Exception as e:
        print(f"Error al crear usuario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
