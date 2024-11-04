from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    html_content = """
    <html>
        <head>
            <title>PyPack Trends</title>
        </head>
        <body>
            <h3>PyPack Trends 🐍 coming soon!</h3>
        </body>
    </html>
    """
    return html_content


@app.get("/health-check/")
async def health_check() -> bool:
    return True
