import requests

API_URL = "http://25.18.122.76:3030/api/v1/prediction/138d0525-a09b-4889-9bfd-7de734bdd03c"
headers = {
    "Authorization": "Bearer J1sIK83AjwdnvIo2i4kwkWU4061C0ugZF2K5ngpgO2Y"
}

def get_image_discription(payload):
    output = {'question': payload}
    response = requests.post(API_URL, headers=headers,json=output )
    response = response.json()
    print( response)
    response = response['json']['answer']
    print( response)
    return response

if __name__ == '__main__':
    content = "你叫什么？"
    get_image_discription(content)