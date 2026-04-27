import uvicorn


def dev() -> None:
    uvicorn.run("src.main:app", reload=True, host="0.0.0.0", port=8080)
