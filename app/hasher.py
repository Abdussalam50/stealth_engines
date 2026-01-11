from passlib.context import CryptContext

pwd_context=CryptContext(schemes=['sha256_crypt'],deprecated='auto')

def hash_pass(password:str):
    return pwd_context.hash(password)

def verify_pass(plain_pass,hashed_pass):
    return pwd_context.verify(plain_pass,hashed_pass)