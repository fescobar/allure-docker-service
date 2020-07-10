# This directory is where you have all your results locally, generally named as `allure-results`
$ReportPath="allure-results-example"
# This url is where the Allure container is deployed. We are using localhost as example
$BaseUrl = "http://localhost:5050"
# Project ID according to existent projects in your Allure container - Check endpoint for project creation >> `[POST]/projects`
$ProjectId="default"
#$ProjectId="my-project-id"

$Request = @{
  "results" = @()
}

$Files = (Get-ChildItem -File -Path "$PSScriptRoot\$ReportPath")
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

Write-Output "------------------SEND-RESULTS------------------"
$SendResultsEndpoint="$BaseUrl/send-results?project_id=$ProjectId"
$result = Invoke-WebRequest -Uri $SendResultsEndpoint -ContentType 'application/json' -Method POST -Body $json -UseBasicParsing
Write-Output "Status Code:" $result.StatusCode
Write-Output "Response: " $result.Content

<#
#If you want to generate reports on demand use the endpoint `GET /generate-report` and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
Write-Output "------------------GENERATE-REPORT------------------"
$ExecutionName ="execution_from_my_ps_script"
$ExecutionFrom ="http://google.com"
$ExecutionType = "bamboo"

$GenerateReportEndpoint="$BaseUrl/generate-report?project_id=$ProjectId"
$response = Invoke-RestMethod -Uri "$GenerateReportEndpoint&execution_name=$ExecutionName&execution_from=$ExecutionFrom&execution_type=$ExecutionType"
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
#>
