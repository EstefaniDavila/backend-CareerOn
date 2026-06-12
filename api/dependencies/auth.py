import base64
import json
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Dependencia de FastAPI para extraer el usuario desde el Token MSAL enviado por React.
    NOTA HACKATHON: Para ganar velocidad, decodificamos el JWT manualmente y confiamos 
    en los datos que Microsoft nos envía sin validar la firma criptográfica con Azure.
    """
    token = credentials.credentials
    
    try:
        # Un JWT consta de 3 partes separadas por puntos. La del medio es el payload.
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Formato de token inválido")
            
        payload_b64 = parts[1]
        
        # Añadir padding si es necesario para el formato base64
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        payload_data = json.loads(payload_json)
        
        # MSAL suele devolver 'preferred_username' o 'email' o 'upn'
        email = payload_data.get("preferred_username") or payload_data.get("email") or payload_data.get("upn")
        name = payload_data.get("name")
        
        if not email:
            raise HTTPException(status_code=401, detail="El token no contiene un email válido.")
            
        return {
            "email": email,
            "name": name,
            "raw_payload": payload_data
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido o expirado: {str(e)}")
