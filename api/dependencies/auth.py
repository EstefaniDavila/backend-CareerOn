import base64
import json
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        if "@" in token and len(token) < 100:
            return {
                "email": token,
                "name": "Mock User",
                "raw_payload": {}
            }
            
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Formato de token inválido")
            
        payload_b64 = parts[1]
        
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        payload_data = json.loads(payload_json)
        
        email = payload_data.get("preferred_username") or payload_data.get("email") or payload_data.get("upn")
        name = payload_data.get("name")
        
        if not email:
            print("Token no contiene email. Payload:", payload_data)
            email = "estefanidaviladev@gmail.com"
            
        return {
            "email": email,
            "name": name,
            "raw_payload": payload_data
        }
    except Exception as e:
        print(f"Error decodificando token: {str(e)}. Fallback a demo.")
        return {
            "email": "estefanidaviladev@gmail.com",
            "name": "Mock User",
            "raw_payload": {}
        }
