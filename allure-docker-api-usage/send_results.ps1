# Location of the report
$ReportPath=".\allure-results-example"
# Name of the project
$ProjectId="default"
# Url of allure reporting (without a trailing /)
$BaseUrl = "http://localhost:5050"
# Execution Name
$ExecutionName ="mgtest"
# Exection From
$ExecutionFrom ="local"

$SendResultsEndpoint="$BaseUrl/send-results?project_id=$ProjectId"
$GenerateReportEndpoint="$BaseUrl/generate-report?project_id=$ProjectId"

$Request = @{
  "results" = @()
}

$Files = (Get-ChildItem -File -Path $ReportPath)
foreach ($Item in $Files) {    
    $Content = Get-Content -Path $Item.FullName
    if ($Content){
        $Result = @{
          "file_name"= $Item.name
          "content_base64"= [Convert]::ToBase64String([IO.File]::ReadAllBytes($Item.FullName))
        }
        $Request.results += $Result;
    }
}

$json = ConvertTo-Json -InputObject $Request

$result = Invoke-WebRequest -Uri $SendResultsEndpoint -ContentType 'application/json' -Method POST -Body $json -UseBasicParsing

$response = Invoke-RestMethod -Uri "$GenerateReportEndpoint&ExecutionName=$ExecutionName&execution_from=$ExecutionFrom&executionType=test"
$reportUrl = $response.data.report_url
$testreport = @"
_________________________________________________________________________________________________
 _____         _                               _   
|_   _|       | |                             | |  
  | | ___  ___| |_   _ __ ___ _ __   ___  _ __| |_ 
  | |/ _ \/ __| __| | '__/ _ \ '_ \ / _ \| '__| __|
  | |  __/\__ \ |_  | | |  __/ |_) | (_) | |  | |_ 
  \_/\___||___/\__| |_|  \___| .__/ \___/|_|   \__|
                             | |                   
                             |_|                   
_________________________________________________________________________________________________

$reportUrl 
_________________________________________________________________________________________________
"@

Write-Output $testreport