from fastapi.security import OAuth2PasswordBearer

oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/user/token", scheme_name="User")