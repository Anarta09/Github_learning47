# headers.py
class Headers:
    @staticmethod
    def get_json_headers(token: str) -> dict:
        """Generate standard headers for JSON requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
