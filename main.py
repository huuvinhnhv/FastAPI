from fastapi import FastAPI
from web3 import Web3
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request
import requests
from fastapi import Header, HTTPException
from fastapi import Depends
from typing import Dict
import json
import time

app = FastAPI(title="Random Number Generator")

# Define a CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# redirect to the docs
@app.get("/", tags=["Docs"])
async def redirect_docs():
    return RedirectResponse("http://localhost:8000/docs")

# Define a sample endpoint
# @app.get("/token")
# async def get_beaver_token():
#     url = "https://raas.deta.dev/token"
#     data = "username=demo&password=demo"
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     response = requests.post(url, data=data, headers=headers)
#     beaver_token = response.json().get("access_token")
#     print(f"Status code: {response.status_code}")
#     return beaver_token

# @app.get("/token")


async def get_beaver_token():
    url = "https://raas.deta.dev/token"
    data = "username=demo&password=demo"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)
    beaver_token = response.json().get("access_token")
    print(f"Status code: {response.status_code}")
    return beaver_token


async def get_auth_header():
    token = await get_beaver_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    else:
        raise HTTPException(status_code=401, detail="Unable to authenticate")


@app.post("/getRequestId", tags=["GET Request Id"])
async def get_request_id(auth_header: dict = Depends(get_auth_header)):
    url = "https://raas.deta.dev/random"
    request_body = {
        "numWords": 1,
        "callBackUrl": "https://raasdemo.deta.dev/fulfilment"
    }
    response = requests.post(url, json=request_body, headers=auth_header)
    return response.json()


@app.get("/getRandomNumber/{requestId}", tags=["GET data by request Id"])
async def read_data_by_request_id(requestId: int):
    url = f"https://raas.deta.dev/draw/{requestId}"
    count = 0
    try:
        while True:
            response = requests.get(url)
            time.sleep(5)
            count += 5
            print(count)
            if response.status_code == 200:
                break
    except requests.exceptions.HTTPError as e:
        return ({e.response.status_code})
    except requests.exceptions.Timeout:
        return ("Request timed out")
    num = int(response.json()[0].get("randomWords")[1:-1])
    address = '0x7a1bac17ccc5b313516c5e16fb24f7659aa5ebed'
    apiKey = 'YV328YDS74FSM4YHYVFEXVJN9PBRJCWQUQ'

    blockTimeStamp = int(response.json()[0].get("timestamp"))
    blockUrl = f'https://api-testnet.polygonscan.com/api?module=block&action=getblocknobytime&timestamp={blockTimeStamp}&closest=before&apikey={apiKey}'
    blockNo = requests.get(blockUrl).json().get('result')
    # print(blockNo)

    # get txHash of block
    logUrl = f'https://api-testnet.polygonscan.com/api?module=logs&action=getLogs&fromBlock={blockNo}&toBlock={blockNo}&address={address}&apikey={apiKey}'

    arr = requests.get(logUrl).json().get('result')
    for data in arr:
        tempRequestId = data.get('data')[0:66]
        if requestId == Web3.to_int(hexstr=tempRequestId):
            txHash = data.get("transactionHash")
    link = f"https://mumbai.polygonscan.com/tx/{txHash}#eventlog"

    return {"randomNum": response.json()[0].get("randomWords")[1:-1],
            "mappingNum": num % 20+1,
            "transectionLog": link}


@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs"
    )


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title="API Docs",
        version="0.0.1",
        description="This is a test API",
        routes=app.routes,
    )

app.mount("/static", StaticFiles(directory="static"), name="static")
