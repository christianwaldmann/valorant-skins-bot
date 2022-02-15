import re
import aiohttp
import json

from dotenv import load_dotenv


load_dotenv()


async def store(username, password, region):
    headers, user_id = await get_user_data(username, password)
    session = aiohttp.ClientSession()
    async with session.get(
        f"https://pd.{region}.a.pvp.net/store/v2/storefront/{user_id}", headers=headers
    ) as r:
        data = json.loads(await r.text())
    await session.close()
    skinPanel = data["SkinsPanelLayout"]
    return await get_single_offer_details(headers, skinPanel, region)


async def nightmarket(username, password, region):
    headers, user_id = await get_user_data(username, password)
    session = aiohttp.ClientSession()
    async with session.get(
        f"https://pd.{region}.a.pvp.net/store/v2/storefront/{user_id}", headers=headers
    ) as r:
        data = json.loads(await r.text())
    await session.close()
    bundle = data["BonusStore"]
    return await get_nightmarket_details(headers, bundle)


async def get_user_data(username, password):
    session = aiohttp.ClientSession()
    data = {
        "client_id": "play-valorant-web-prod",
        "nonce": "1",
        "redirect_uri": "https://playvalorant.com/opt_in",
        "response_type": "token id_token",
    }
    headers = {"Accept": "*/*", "User-Agent": username}

    try:
        await session.post(
            "https://auth.riotgames.com/api/v1/authorization",
            json=data,
            headers=headers,
        )
    except Exception as e:
        print(e)
    data = {"type": "auth", "username": username, "password": password}
    try:
        async with session.put(
            "https://auth.riotgames.com/api/v1/authorization",
            json=data,
            headers=headers,
        ) as r:
            data = await r.json()
        await session.close()
    except Exception as e:
        print(e)
    try:
        if "type" in data:
            if data["type"] == "multifactor":
                return 405, 405
        if "error" in data:
            if data["error"] == "auth_failure":
                return 403, 403
            elif data["error"] == "rate_limited":
                return 429, 429
        pattern = re.compile(
            "access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)"
        )
        data = pattern.findall(data["response"]["parameters"]["uri"])[0]
        access_token = data[0]

        headers = {"Authorization": f"Bearer {access_token}", "User-Agent": username}
        session = aiohttp.ClientSession()
        try:
            async with session.post(
                "https://entitlements.auth.riotgames.com/api/token/v1",
                headers=headers,
                json={},
            ) as r:
                data = await r.json()
        except Exception as e:
            print(e)
        entitlements_token = data["entitlements_token"]
        try:
            async with session.post(
                "https://auth.riotgames.com/userinfo", headers=headers, json={}
            ) as r:
                data = await r.json()
            await session.close()
        except Exception as e:
            print(e)

        user_id = data["sub"]
        headers["X-Riot-Entitlements-JWT"] = entitlements_token
        headers[
            "X-Riot-ClientPlatform"
        ] = "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9"
        headers["X-Riot-ClientVersion"] = "pbe-shipping-55-604424"
        return (headers, user_id)
    except Exception as e:
        print(e)


async def get_single_offer_details(headers, skinPanel, region):
    skinIDcost = []
    skinNames = []
    offerSkins = []

    session = aiohttp.ClientSession()

    async with session.get(
        f"https://pd.{region}.a.pvp.net/store/v1/offers/", headers=headers
    ) as r:
        offers = json.loads(await r.text())

    for item in skinPanel["SingleItemOffers"]:
        async with session.get(
            f"https://valorant-api.com/v1/weapons/skinlevels/{item}", headers=headers
        ) as r:
            content = json.loads(await r.text())
            skinNames.append(
                {
                    "id": content["data"]["uuid"].lower(),
                    "name": content["data"]["displayName"],
                }
            )

    await session.close()

    for item in offers["Offers"]:
        if skinPanel["SingleItemOffers"].count(item["OfferID"].lower()) > 0:
            skinIDcost.append(
                {"id": item["OfferID"].lower(), "cost": list(item["Cost"].values())[0]}
            )

    for item in skinNames:
        for item2 in skinIDcost:
            if item["id"] in item2["id"]:
                offerSkins.append(
                    [
                        item["name"],
                        item2["cost"],
                        f"https://media.valorant-api.com/weaponskinlevels/{item['id']}/displayicon.png",
                    ]
                )
    return (
        offerSkins,
        convert_seconds_to_output_str(
            skinPanel["SingleItemOffersRemainingDurationInSeconds"]
        ),
    )


async def get_nightmarket_details(headers, bundle):
    offerSkins = []

    session = aiohttp.ClientSession()

    for item in bundle["BonusStoreOffers"]:
        skin_id = item["Offer"]["OfferID"]
        async with session.get(
            f"https://valorant-api.com/v1/weapons/skinlevels/{skin_id}",
            headers=headers,
        ) as r:
            content = json.loads(await r.text())
            skin_name = content["data"]["displayName"]
            skin_discounted_price = list(item["DiscountCosts"].values())[0]
            skin_original_price = list(item["Offer"]["Cost"].values())[0]
            offerSkins.append(
                [
                    skin_name,
                    skin_discounted_price,
                    f"https://media.valorant-api.com/weaponskinlevels/{skin_id}/displayicon.png",
                    item["DiscountPercent"],
                    skin_original_price,
                ]
            )

    await session.close()

    return (
        offerSkins,
        convert_seconds_to_output_str(bundle["BonusStoreRemainingDurationInSeconds"]),
    )


def convert_seconds_to_output_str(seconds):
    days = seconds // (3600 * 24)
    seconds %= 24 * 3600
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    if days == 0:
        output_str = f"{hour} hours and {minutes} minutes"
    else:
        output_str = f"{days} days, {hour} hours and {minutes} minutes"
    return output_str
