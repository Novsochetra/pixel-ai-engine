from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class UiFiles(StaticFiles):
    # The UI routes screens in the browser, so /library must load index.html, not a 404.
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404 or path.startswith("api/"):
                raise

            return await super().get_response("index.html", scope)
