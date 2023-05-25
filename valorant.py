import re
from typing import List, Optional, NewType
import aiohttp
import json
from dataclasses import dataclass


class AuthenticationError(Exception):
    pass


@dataclass
class AccessToken:
    value: str
    id: str


@dataclass
class Skin:
    name: str
    id: str


@dataclass
class Offer:
    skin: Skin
    cost: int
    image_url: str


@dataclass
class Store:
    offers: List[Offer]
    remaining_duration_in_seconds: int


EntitlementsToken = NewType("EntitlementsToken", str)
Region = NewType("Region", str)
UserId = NewType("UserId", str)


class AuthenticatedValorantClient:
    def __init__(
        self,
        access_token: AccessToken,
        entitlements_token: EntitlementsToken,
        user_id: UserId,
        headers: dict,
        region: Region,
    ) -> None:
        self.access_token = access_token
        self.entitlements_token = entitlements_token
        self.user_id = user_id
        self.headers = headers
        self.region = region

    async def get_store(self) -> Store:
        session = aiohttp.ClientSession()
        async with session.get(
            f"https://pd.{self.region}.a.pvp.net/store/v2/storefront/{self.user_id}",
            headers=self.headers,
        ) as r:
            data = json.loads(await r.text())
        await session.close()
        skin_panel = data["SkinsPanelLayout"]
        skin_ids = skin_panel["SingleItemOffers"]
        offers = []
        for i, skin_id in enumerate(skin_ids):
            skin = await self._get_skin(skin_id)
            cost = next(iter(skin_panel["SingleItemStoreOffers"][i]["Cost"].values()))
            image_url = self._get_skin_image_url(skin_id)
            offer = Offer(skin=skin, cost=cost, image_url=image_url)
            offers.append(offer)
        remaining_duration_in_seconds = skin_panel[
            "SingleItemOffersRemainingDurationInSeconds"
        ]
        return Store(
            offers=offers, remaining_duration_in_seconds=remaining_duration_in_seconds
        )

    async def _get_skin(self, skin_id: str) -> Skin:
        session = aiohttp.ClientSession()
        async with session.get(
            f"https://valorant-api.com/v1/weapons/skinlevels/{skin_id}",
            headers=self.headers,
        ) as r:
            content = json.loads(await r.text())
        await session.close()
        skin = Skin(
            name=content["data"]["displayName"], id=content["data"]["uuid"].lower()
        )
        return skin

    def _get_skin_image_url(self, skin_id: str) -> str:
        return (
            f"https://media.valorant-api.com/weaponskinlevels/{skin_id}/displayicon.png"
        )


class ValorantClient:
    async def authenticate(
        self, username: str, password: str
    ) -> Optional[AuthenticatedValorantClient]:
        access_token = await self._get_access_token(username, password)
        entitlements_token = await self._get_entitlements_token(access_token)
        user_info = await self._get_user_info(access_token)
        headers = self._build_headers(access_token, entitlements_token)
        region = await self._get_region(access_token)
        return AuthenticatedValorantClient(
            access_token, entitlements_token, user_info, headers, region
        )

    async def _get_access_token(self, username: str, password: str) -> AccessToken:
        session = aiohttp.ClientSession()
        data = {
            "client_id": "play-valorant-web-prod",
            "nonce": "1",
            "redirect_uri": "https://playvalorant.com/opt_in",
            "response_type": "token id_token",
            "scope": "account openid",
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "RiotClient/60.0.6.4770705.4749685 rso-auth (Windows;10;;Professional, x64)",
            "Content-Type": "application/json",
        }
        await session.post(
            "https://auth.riotgames.com/api/v1/authorization",
            json=data,
            headers=headers,
        )
        data = {
            "type": "auth",
            "username": username,
            "password": password,
        }
        async with session.put(
            "https://auth.riotgames.com/api/v1/authorization",
            json=data,
            headers=headers,
        ) as r:
            data = await r.json()
        await session.close()

        if data["type"] == "response":
            pattern = re.compile(
                "access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)"
            )
            data = pattern.findall(data["response"]["parameters"]["uri"])[0]
            return AccessToken(value=data[0], id=data[1])

        elif data["type"] == "multifactor":
            if r.status == 429:
                raise AuthenticationError(
                    "Ratelimit. Please wait a few minutes and try again."
                )

            # Two-factor authentication is enabled. So get verification code and authenticate with that
            verification_code = input(
                f"Two-factor authentication enabled for user {username}. Enter the verification code: \n"
            )
            authdata = {
                "type": "multifactor",
                "code": verification_code,
            }
            session = aiohttp.ClientSession()
            async with session.put(
                "https://auth.riotgames.com/api/v1/authorization",
                json=authdata,
                headers=headers,
            ) as r:
                data = await r.json()
            await session.close()
            if data["type"] == "response":
                pattern = re.compile(
                    "access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)"
                )
                data = pattern.findall(data["response"]["parameters"]["uri"])[0]
                return AccessToken(value=data[0], id=data[1])

        raise AuthenticationError(
            "Invalid password. Your username or password may be incorrect!"
        )

    async def _get_entitlements_token(
        self, access_token: AccessToken
    ) -> EntitlementsToken:
        headers = {
            "Authorization": f"Bearer {access_token.value}",
            "Content-Type": "application/json",
        }
        session = aiohttp.ClientSession()
        async with session.post(
            "https://entitlements.auth.riotgames.com/api/token/v1",
            headers=headers,
            json={},
        ) as r:
            data = await r.json()
        await session.close()
        entitlements_token = data["entitlements_token"]
        return entitlements_token

    async def _get_user_info(self, access_token: AccessToken) -> UserId:
        headers = {
            "Authorization": f"Bearer {access_token.value}",
            "Content-Type": "application/json",
        }
        session = aiohttp.ClientSession()
        async with session.post(
            "https://auth.riotgames.com/userinfo", headers=headers, json={}
        ) as r:
            data = await r.json()
        await session.close()
        user_id = data["sub"]
        return UserId(user_id)

    def _build_headers(
        self, access_token: AccessToken, entitlements_token: EntitlementsToken
    ) -> dict:
        return {
            "Authorization": f"Bearer {access_token.value}",
            "Content-Type": "application/json",
            "X-Riot-Entitlements-JWT": entitlements_token,
        }

    async def _get_region(self, access_token: AccessToken) -> Region:
        headers = {
            "Authorization": f"Bearer {access_token.value}",
            "Content-Type": "application/json",
        }
        body = {"id_token": access_token.id}
        session = aiohttp.ClientSession()
        async with session.put(
            "https://riot-geo.pas.si.riotgames.com/pas/v1/product/valorant",
            headers=headers,
            json=body,
        ) as r:
            data = await r.json()
        await session.close()
        try:
            region = data["affinities"]["live"]
        except KeyError:
            raise AuthenticationError("Region not found. An unknown error occurred")
        return Region(region)
