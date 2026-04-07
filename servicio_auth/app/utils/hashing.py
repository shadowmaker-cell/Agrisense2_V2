import bcrypt

def hashear_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False