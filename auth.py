from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AUTH_TOKEN

# Setup the bearer authentication scheme
bearer_scheme = HTTPBearer()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Validate the authentication token in the request.
    
    Args:
        credentials: The credentials extracted from the Authorization header
        
    Returns:
        True if the token is valid
        
    Raises:
        HTTPException: If the token is invalid or missing
    """
    if credentials.scheme != "Bearer" or credentials.credentials != AUTH_TOKEN:
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication token"
        )
    return True