import atexit
import base64
import hashlib
import json
import os
import aiohttp
from cryptography.fernet import Fernet



class Json(dict):
    def __init__(self, path):
        self._path = path
        with open(os.path.join('data', path), 'r') as f:
            file = json.load(f)
        for key in file:
            self[key] = file[key]
        atexit.register(self.save)
    
    def save(self):
        with open(self._path, 'w') as f:
            json.dump(self, f, indent=4)



class DBJson:
    def __init__(self):
        self.url = os.getenv("TDBW_URL")
        self.password = hashlib.sha1(os.getenv("TDBW_PASSWORD").encode("utf-8")).hexdigest()
        bpassword = base64.urlsafe_b64encode(os.getenv("TDBW_PASSWORD")[:32].encode("utf-8"))
        self.key = Fernet(bpassword)

    async def _get(self, keyvals, method="search"):
        async with aiohttp.ClientSession() as session:
            json={
                "password": self.password,
                "method": method,
                "params": self.key.encrypt(str(keyvals).encode("utf-8")).decode("utf-8")
            }
            async with session.get(self.url, json=json) as resp:
                resp_json = await resp.json()

        if not resp_json.get("success"):
            return None
        result = resp_json["result"]
        return eval(self.key.decrypt(result.encode("utf-8")))

    async def get(self, **kw):
        return await self._get(kw, method="search")

    async def insert(self, json):
        return await self._get(json, method="insert")

    async def remove(self, **kw):
        return await self._get(kw, method="remove")

    async def update(self, updated_vals, **kw):
        return await self._get({"value": updated_vals, "keys": kw}, method="update")

    async def all(self):
        return await self._get({}, method="all")
    
    async def op(self, ops, **kw):
        return await self._get([(x, "==", y) for x, y in kw.items()] + ops, method="op-search")

    async def find(self, subset, superset, **kw):
        return await self._get({"find": subset, "find-item": superset, "frag": kw}, method="find-search")

    async def top(self, attribute, amount, **kw):
        return await self._get({"greatest": attribute, "max": amount, "frag": kw}, method="top-search")
