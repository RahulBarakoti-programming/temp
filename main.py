import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from helpers.execute_python_code import execute_python_code

from helpers.analyze_error_with_ai import analyze_error_with_ai
load_dotenv()

app = FastAPI()


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeRequest(BaseModel):
    code: str


@app.post("/code-interpreter")
def interpret_code(request: CodeRequest):
    # 1. Execute the Python code
    execution = execute_python_code(request.code)

    # 2. If execution was successful, don't call AI
    if execution["success"]:
        return {
            "error": [],
            "result": execution["output"],
        }

    # 3. If execution failed, ask AI to identify error lines
    try:
        error_lines = analyze_error_with_ai(
            request.code,
            execution["output"],
        )
    except Exception:
        # AI down/quota/retired model: fall back to the traceback instead of a CORS-less 500
        lines = re.findall(r'File "<string>", line (\d+)', execution["output"])
        error_lines = [int(lines[-1])] if lines else []

    # 4. Return the exact execution output + AI error lines
    return {
        "error": error_lines,
        "result": execution["output"],
    }