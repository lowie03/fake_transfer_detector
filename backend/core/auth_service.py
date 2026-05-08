import hashlib
import uuid


def _hash(password: str) -> str:
    """
    Hash a password using SHA-256 with a fixed salt prefix.
    NOTE: For production, upgrade to bcrypt or argon2. This uses a salted
    SHA-256 as a pragmatic improvement over raw SHA-256 for a prototype.
    """
    salted = f"transfernet$${password}"
    return hashlib.sha256(salted.encode()).hexdigest()


# In-memory user store  — replace with a real database for production
_USERS: dict[str, dict] = {
    "demo@transfernet.ai": {
        "id": "demo-001",
        "name": "Demo User",
        "business_name": "Demo Store",
        "email": "demo@transfernet.ai",
        "phone": "08012345678",
        "password_hash": _hash("demo1234"),
    }
}

# token → email mapping  (stateless placeholder — use JWT in production)
_TOKENS: dict[str, str] = {}


def authenticate(email: str, password: str) -> dict | None:
    user = _USERS.get(email.lower().strip())
    if user and user["password_hash"] == _hash(password):
        return user
    return None


def register(name: str, business_name: str, email: str, phone: str, password: str) -> dict | None:
    key = email.lower().strip()
    if key in _USERS:
        return None  # already exists
    user_id = str(uuid.uuid4())
    _USERS[key] = {
        "id": user_id,
        "name": name,
        "business_name": business_name,
        "email": key,
        "phone": phone,
        "password_hash": _hash(password),
    }
    return _USERS[key]


def create_token(email: str) -> str:
    token = str(uuid.uuid4())
    _TOKENS[token] = email.lower().strip()
    return token


def get_user_by_token(token: str) -> dict | None:
    email = _TOKENS.get(token)
    if email:
        return _USERS.get(email)
    return None


def update_user(token: str, updates: dict) -> dict | None:
    user = get_user_by_token(token)
    if not user:
        return None
    email = user["email"]
    for key, val in updates.items():
        if key in ("name", "business_name", "phone"):
            _USERS[email][key] = val
        elif key == "password_hash":
            _USERS[email]["password_hash"] = val
    return _USERS[email]
