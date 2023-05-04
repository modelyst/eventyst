from fastapi import APIRouter, Depends

router = APIRouter()


def test_dependency():
    return 1


@router.get("/test", dependencies=[Depends(test_dependency)])
async def test(x=Depends(lambda: 1)):
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("test:router")
