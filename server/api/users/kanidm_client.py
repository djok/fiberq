import logging

import httpx

from config import settings

logger = logging.getLogger("fiberq.users.kanidm")


class KanidmAdminClient:
    """Async Kanidm REST API client using a service account API token.

    All mutations go through the Kanidm V1 JSON API.  Errors are left as
    ``httpx.HTTPStatusError`` so the calling route can map them to
    appropriate HTTP responses.
    """

    def __init__(self) -> None:
        self.base_url = settings.kanidm_url.rstrip("/")
        self.token = settings.kanidm_api_token
        self.verify_tls = settings.kanidm_verify_tls

    def _headers(self, mutation: bool = False) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if mutation:
            headers["Content-Type"] = "application/json"
        return headers

    # ------------------------------------------------------------------
    # Person operations
    # ------------------------------------------------------------------

    async def list_persons(self) -> list[dict]:
        """GET /v1/person -- list all person entries."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def get_person(self, id: str) -> dict:
        """GET /v1/person/{id} -- get a single person."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person/{id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def create_person(self, username: str, display_name: str) -> None:
        """POST /v1/person -- create a new person entry."""
        body = {
            "attrs": {
                "name": [username],
                "displayname": [display_name],
            }
        }
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.post(
                f"{self.base_url}/v1/person",
                headers=self._headers(mutation=True),
                json=body,
            )
            resp.raise_for_status()

    async def set_person_attr(
        self, id: str, attr: str, values: list[str]
    ) -> None:
        """PUT /v1/person/{id}/_attr/{attr} -- set an attribute."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.put(
                f"{self.base_url}/v1/person/{id}/_attr/{attr}",
                headers=self._headers(mutation=True),
                json=values,
            )
            resp.raise_for_status()

    async def delete_person_attr(self, id: str, attr: str) -> None:
        """DELETE /v1/person/{id}/_attr/{attr} -- remove an attribute."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.delete(
                f"{self.base_url}/v1/person/{id}/_attr/{attr}",
                headers=self._headers(),
            )
            resp.raise_for_status()

    async def deactivate_person(self, id: str) -> None:
        """Set account_expire to epoch to disable a person."""
        await self.set_person_attr(
            id, "account_expire", ["1970-01-01T00:00:00+00:00"]
        )

    async def reactivate_person(self, id: str) -> None:
        """Remove account_expire to re-enable a person."""
        await self.delete_person_attr(id, "account_expire")

    async def create_credential_reset_token(
        self, id: str, ttl: int = 3600
    ) -> str:
        """GET /v1/person/{id}/_credential/_update_intent/{ttl}."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person/{id}/_credential/_update_intent/{ttl}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Group operations
    # ------------------------------------------------------------------

    async def get_group_members(self, group_name: str) -> list[str]:
        """GET /v1/group/{group_name}/_attr/member -- list members."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/group/{group_name}/_attr/member",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def add_group_member(
        self, group_name: str, member_id: str
    ) -> None:
        """POST /v1/group/{group_name}/_attr/member -- add a member."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.post(
                f"{self.base_url}/v1/group/{group_name}/_attr/member",
                headers=self._headers(mutation=True),
                json=[member_id],
            )
            resp.raise_for_status()

    async def set_group_members(
        self, group_name: str, members: list[str]
    ) -> None:
        """PUT /v1/group/{group_name}/_attr/member -- replace members."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.put(
                f"{self.base_url}/v1/group/{group_name}/_attr/member",
                headers=self._headers(mutation=True),
                json=members,
            )
            resp.raise_for_status()

    async def remove_group_member(
        self, group_name: str, member_id: str
    ) -> None:
        """Remove a single member from a group.

        Fetches current members, filters out the target, then PUTs the
        remaining list.  If no members remain, DELETEs the attribute.
        """
        current = await self.get_group_members(group_name)
        remaining = [m for m in current if m != member_id]

        if remaining:
            await self.set_group_members(group_name, remaining)
        else:
            # No members left -- remove the attribute entirely
            async with httpx.AsyncClient(verify=self.verify_tls) as client:
                resp = await client.delete(
                    f"{self.base_url}/v1/group/{group_name}/_attr/member",
                    headers=self._headers(),
                )
                resp.raise_for_status()
