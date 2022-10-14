import asyncio
import aiofiles
import uvloop
import httpx
import os

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Couchi:
    def __init__(
        self,
        db: str = "hello-there",
        root_url: str = os.environ["URL"],
        username: str = os.environ["USERNAME"],
        password: str = os.environ["PASSWORD"],
    ):
        self.db = db
        self.root_url = root_url
        self.username = username
        self.password = password
        self.db_url = f"http://{root_url}/{db}"

    async def __aenter__(self):
        timeout = httpx.Timeout(6, read=15)
        self.client = httpx.AsyncClient(timeout=timeout)
        return self

    async def __aexit__(self, a, b, c):
        await self.client.aclose()

    async def _req(
        self,
        url: str,
        method: str = "get",
        headers: [None | dict] = None,
        data: [None | dict] = None,
        bin_data: [None | bytes] = None,
    ):
        if method == "put" and bin_data is not None:
            await self.client.request(method, url, content=bin_data)
        if method == "put" and data is not None:
            await self.client.put(url, json=data)
        else:
            await self.client.request(method, url)

    async def _check(self, res):
        j = res.json()
        if res.status_code == httpx.codes.OK:
            return (True, j)
        elif "error" in j and j["error"] == "conflict":
            return (True, f"{res.url} already exists")
        else:
            if "error" in j and j["error"] == "not_found":
                return (False, j["error"])
            else:
                return (False, j)

    async def create_db(self):
        res = await self.client.put(self.db_url, params={"db": self.db})
        return await self._check(res)

    async def add(
        self,
        doc_id: str = "testing-doc",
        doc_data: dict = {"id": "testing-doc", "data": "hi there"},
        recursed: int = 0,
    ):
        if recursed == 2:
            return (False, "recursed limit reached")
        res = await self.client.put(f"{self.db_url}/{doc_id}", json=doc_data)
        r = await self._check(res)
        if r[0]:
            return r[1]
        elif not r[0] and r[1] == "not_found":
            cdb = await self.create_db()
            if cdb:
                await self.add(doc_id, doc_data, recursed + 1)
            else:
                return (False, f"{self.db} could not be made for {cdb[1]}")
        else:
            return r

    async def get(self, doc_id: str = "testing-doc"):
        res = await self.client.get(f"{self.db_url}/{doc_id}")
        return await self._check(res)

    async def head(self, doc_id: str = "testing-doc"):
        res = await self.client.head(f"{self.db_url}/{doc_id}")
        return res.headers

    async def delete(self, doc_id: str = "testing-doc"):
        res = await self.client.delete(f"{self.db_url}/{doc_id}")
        return await self._check(res)

    async def get_cur_rev(self, doc_id: str):
        res = await self.head(doc_id)
        return res["ETag"]

    async def attach(
        self, data, doc_id: str = "testing-doc", attach_id: str = "testing-attachment"
    ):
        rev = await self.get_cur_rev(doc_id)
        print(type(data))
        res = await self.client.put(
            f"{self.db_url}/{doc_id}/{attach_id}",
            headers={"If-Match": rev},
            content=data,
        )
        return res

    async def attach_file(
        self,
        filename: str = "testing.txt",
        doc_id: str = "testing-doc",
        attach_id: str = "testing-attachment2",
        file_size_limit: int = 500000000,
    ):
        if os.path.isfile(filename):
            file_size = os.path.getsize(filename)
            if file_size < file_size_limit:
                async with aiofiles.open(filename, "rb") as f:
                    data = await f.read()
                    res = await self.attach(data, doc_id, attach_id)
                    return await self._check(res)
            else:
                return (False, f"{filename} is {file_size} > {file_size_limit}")

    async def get_attach(
        self,
        doc_id: str = "testing-doc",
        attach_id: str = "testing-attachment2",
    ):
        res = await self.client.get(f"{self.db_url}/{doc_id}/{attach_id}")
        return res

    async def get_session_auth(
        self,
    ):
        url = f"http://{self.root_url}/_session"
        res = await self.client.post(
            url, json={"name": self.username, "password": self.password}
        )
        if "ok" in res.json():
            return (True, res.headers["Set-Cookie"])
        else:
            return (False, res.json())

    async def get_all(self, params: dict = {"include_docs": True}):
        res = await self.client.get(
            f"{self.db_url}/_all_docs",
            params=params,
        )
        return res.json()

    async def get_cookies(self):
        return self.client.cookies


async def main():
    async with Couchi("timmy") as timmy:
        await timmy.get_session_auth()
        doc = await timmy.add()
        print(doc)
        p = await timmy.get_all()
        print(p)
        f = await timmy.attach_file()
        print(f)
        g = await timmy.get_attach()
        print(g.text)


if __name__ == "__main__":
    asyncio.run(main())
