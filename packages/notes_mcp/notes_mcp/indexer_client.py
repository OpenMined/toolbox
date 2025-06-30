import httpx


class IndexerClient(httpx.Client):
    def __init__(self, base_url: str = "http://localhost:8000", *args, **kwargs):
        super().__init__(*args, base_url=base_url, **kwargs)

    def register_user(self, user_email: str, access_token: str):
        """Register a new user or update existing user's access token."""
        return self.post(
            "/register_user",
            json={"email": user_email, "access_token": access_token},
        )

    def healthcheck(self, email: str) -> httpx.Response:
        return self.post("/healthcheck", json={"user_email": email})

    def heartbeat(self, email: str) -> httpx.Response:
        return self.post("/heartbeat", json={"user_email": email})


if __name__ == "__main__":
    print("registering user")
    client = IndexerClient()
    print(client.register_user("koen@openmined.org", "1234567890"))
