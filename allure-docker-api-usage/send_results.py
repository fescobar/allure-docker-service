import os, requests, json, base64

# This directory is where you have all your results locally, generally named as `allure-results`
allureResultsDirectory = '/allure-results-example'
# This url is where the Allure container is deployed. We are using localhost as example
allureServer = 'http://localhost:5050'


currentDirectory = os.path.dirname(os.path.realpath(__file__))
resultsDirectory = currentDirectory + allureResultsDirectory
print('RESULTS DIRECTORY PATH: ' + resultsDirectory)

files = os.listdir(resultsDirectory)

print('FILES:')
results = []
for file in files:
    result = {}

    filePath = resultsDirectory + "/" + file
    print(filePath)

    if os.path.isfile(filePath):
        try:
            with open(filePath, "rb") as f:
                content = f.read()
                if content.strip():
                    b64Content = base64.b64encode(content)
                    result['file_name'] = file
                    result['content_base64'] = b64Content.decode('UTF-8')
                    results.append(result)
                else:
                    print('Empty File skipped: '+ filePath)
        finally :
            f.close()
    else:
        print('Directory skipped: '+ filePath)

headers = {'Content-type': 'application/json'}
requestBody = {
    "results": results
}
jsonRequestBody = json.dumps(requestBody)

response = requests.post(allureServer + '/send-results', headers=headers, data=jsonRequestBody)
print("RESPONSE:")
jsonResponseBody = json.loads(response.content)
jsonPrettierResponseBody = json.dumps(jsonResponseBody, indent=4, sort_keys=True)
print(jsonPrettierResponseBody)
print("STATUS CODE:")
print(response.status_code)
