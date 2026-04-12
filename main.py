import os
import random
import string

import markdown
from fastapi import Depends, FastAPI, File, HTTPException, Security, UploadFile
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from pygments.formatters import HtmlFormatter
from starlette.responses import FileResponse
from starlette.status import HTTP_403_FORBIDDEN

app = FastAPI()

# Read the API key from an environment variable
API_KEY = os.environ.get("API_KEY")

# Ensure that API_KEY environment variable is set
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set.")


# Query parameter API key
API_KEY_QUERY = "api_key"
api_key_query = APIKeyQuery(name=API_KEY_QUERY, auto_error=False)

# Header API key
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

if not os.path.exists("./static"):
    os.makedirs("./static")


# Function to generate a random alphanumeric ID
def generate_random_id(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


# Security dependency for API key authentication
def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API key")


@app.post("/upload_markdown/")
async def upload_markdown(
    file: UploadFile = File(...), api_key: str = Depends(get_api_key)
):
    # Read the uploaded Markdown file content
    markdown_content = await file.read()

    decoded = markdown_content.decode("utf-8")

    # Convert Markdown to HTML
    html_content = markdown.markdown(
        decoded,
        extensions=["tables", "fenced_code", "codehilite"],
        extension_configs={"codehilite": {"guess_lang": True, "linenums": False}},
    )

    # Generate a random alphanumeric ID
    random_id = generate_random_id()

    # Set the desired font family
    font_family = "Arial, sans-serif"

    # code highlight
    css = HtmlFormatter(style="friendly").get_style_defs(".codehilite")

    # Wrap the HTML content with a style tag to set the font family
    html_with_font = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Document</title>
        <style>
            body {{
            font-family: {font_family};
        }}
        {css}
        .codehilite {{
            background: #e0e0e0;
            border-radius: 4px;
            padding: 1em;
            overflow-x: auto;
        }}
        .codehilite pre {{
            margin: 0;
            background: transparent;  /* prevent double background */
        }}
        </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # Save HTML content as a static page
    static_page_path = f"static/{random_id}.html"
    with open(static_page_path, "w") as f:
        f.write(html_with_font)
        f.close()

    # Save HTML content as a static page
    static_md_page_path = f"static/{random_id}.md"
    with open(static_md_page_path, "w") as f:
        f.write(markdown_content.decode("utf-8"))
        f.close()

    # Return the URL to access the static page
    return {"url": f"/static/{random_id}.html"}


@app.get("/static/{file_name}")
async def get_static_page(file_name: str):
    print(file_name)
    # Check if the static file exists
    if not os.path.exists("./static/" + file_name):
        raise HTTPException(status_code=404, detail="File not found")

    # Return the static file
    return FileResponse("./static/" + file_name)
