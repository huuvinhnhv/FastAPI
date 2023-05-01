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
    return RedirectResponse("https://fastapi-17sw.onrender.com/docs")


@app.post("/getRequestId", tags=["GET Request Id"])
async def get_request_id():
    alchemy_url = "https://polygon-mumbai.g.alchemy.com/v2/gtP5XQRh8pmPyr4r5X5az9SLy-wauHKL"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    contract_details = {}
    with open('contract.json') as file:
        contract_details = json.load(file)

    my_address = "0xF3d50eF025A22A991B2972CBA2c5a0cd0a2952Bd"
    private_key = "fc22142cc3ff6a682f291a0dd812068155f764f4932be95ea8b0afac009fcea2"

    contract = w3.eth.contract(address=contract_details.get(
        'address'), abi=contract_details.get('abi'))
    nonce = w3.eth.get_transaction_count(my_address)

    # Build tx for requestRandomWords
    tx = contract.functions.requestRandomWords().build_transaction({
        'chainId': 80001,
        'gas': 2500000,
        'maxFeePerGas': w3.to_wei('2', 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'),
        'nonce': nonce
    })
    # sign with private key
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    # send signed_tx
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # wait for tx to be mined
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # check if tx is successful
    if (tx_receipt.get('status')):
        # process receipt - might fail due to micro timeout of 10s
        requestId = str(contract.events.RequestSent(
        ).process_receipt(tx_receipt)[0]['args']['requestId'])
        return requestId
    else:
        # error
        raise HTTPException(
            status_code=500, detail="Request Not Processed, Kindly try again later")


@app.get("/getRandomNumber/{requestId}", tags=["GET data by request Id"])
def get_ramdom_number(requestId: int):
    alchemy_url = "https://polygon-mumbai.g.alchemy.com/v2/gtP5XQRh8pmPyr4r5X5az9SLy-wauHKL"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))
    contract_details = {}
    with open('contract.json') as file:
        contract_details = json.load(file)

    my_address = "0xF3d50eF025A22A991B2972CBA2c5a0cd0a2952Bd"
    private_key = "fc22142cc3ff6a682f291a0dd812068155f764f4932be95ea8b0afac009fcea2"

    contract = w3.eth.contract(address=contract_details.get(
        'address'), abi=contract_details.get('abi'))
    requests = contract.functions.getRequestStatus(requestId).call()
    if requests[0]:
        random_number = requests[1][0]
        data = {
            "randomNum": str(random_number),
            "mappingNum": random_number % 20+1,
            "transectionLog": "https://mumbai.polygonscan.com/address/0x63855287c54b89b339bb9a715359c7cf307d9c8a"
        }
        return data
    raise HTTPException(
        status_code=500, detail="Request Not Processed, Kindly try again later")
