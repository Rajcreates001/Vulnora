
from .llm_client import get_llm_response, get_embedding
from .code_parser import parse_code_structure
from .file_handler import extract_zip, clone_github_repo, collect_files, cleanup_project_files

# --- Auth utilities for FastAPI ---
from fastapi import Depends, HTTPException, status, Request
from config import settings
import jwt
from jwt import PyJWTError

def verify_jwt_token(request: Request):
	"""Dependency: Verifies JWT in Authorization header."""
	import os
	if os.environ.get("VULNORA_DEV_AUTH_BYPASS", "0") == "1":
		# Bypass JWT check in dev mode
		return {"user": "dev-bypass"}
	auth_header = request.headers.get("Authorization")
	if not auth_header or not auth_header.startswith("Bearer "):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid JWT token")
	token = auth_header.split(" ", 1)[1]
	try:
		payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
		return payload
	except PyJWTError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired JWT token")

def verify_api_key(request: Request):
	"""Dependency: Verifies API key in X-API-Key header."""
	import os
	if os.environ.get("VULNORA_DEV_AUTH_BYPASS", "0") == "1":
		# Bypass API key check in dev mode
		return True
	api_key = request.headers.get("X-API-Key")
	if not api_key or settings.api_key is None or api_key != settings.api_key:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid API key")
	return True
