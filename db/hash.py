from passlib.context import CryptContext

pwd_cxt = CryptContext(schemes=["argon2"], deprecated="auto")

class Hash:

    # def bcrypt(password):
    #     pwd_bytes=password.encode('utf-8')
    #     salt=bcrypt.gensalt()
    #     hashed_password=bcrypt.hashpw(password=pwd_bytes, salt=salt)
    #     return hashed_password
    def bcrypt(password:str):
        return pwd_cxt.hash(password)

    # def verify(hashed_password, plain_password):
    #     password_byte_enc=plain_password.encode('utf-8')
    #     return bcrypt.checkpw(password_byte_enc, hashed_password)
    def verify(hashed_password:str, plain_password:str):
        return pwd_cxt.verify(plain_password, hashed_password)