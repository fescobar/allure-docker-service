<#
.SYNOPSIS
Upload the test results to the Allure Docker Service
#>


param(
    [Parameter(Mandatory)]
    [string]
    #URL pointing to the Allure Service e.g. http://localhost:5050
    $AllureServer,

    [Parameter(Mandatory)]
    [string]
    #Directory path to where the results are stored locally
    $ResultsDir,

    [string]
    #The project ID to upload the results for
    $Project = 'default',

    [switch]
    #Set if you want to force the creation of the project
    $Force,

    [switch]
    #Set if the Allure Docker Service is configure with access credentials
    $Secure,

    [string]
    #Username for the Allure Service
    $Username,

    [string]
    #Password for the Allure Service
    $Password,

    [switch]
    #Set if you do not want to verify SSL
    $NoSSL = $true,

    [switch]
    #Set if you want to generate the report after uploading the results
    $Generate,

    [string]
    #Name of the test execution
    $ExecName,

    [string]
    #URL pointing to the execution
    $ExecFrom,

    [string]
    #Execution type e.g. Jenkins, GitLab etc
    $ExecType
)

if ($NoSSL){
    add-type @"
        using System.Net;
        using System.Security.Cryptography.X509Certificates;
        public class TrustAllCertsPolicy : ICertificatePolicy {
            public bool CheckValidationResult(
                ServicePoint srvPoint, X509Certificate certificate,
                WebRequest request, int certificateProblem) {
                return true;
            }
        }
"@
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
}


if ($Secure){
    $Request = @{
        "username"= $Username
        "password"= $Password
    }
    $LoginEndpoint="$AllureServer/allure-docker-service/login"
    $JsonData = ConvertTo-Json -InputObject $Request
    $response = Invoke-WebRequest -Uri $LoginEndpoint -ContentType 'application/json' -Method POST -Body $JsonData -UseBasicParsing -SessionVariable session
    Write-Output $response.Content
    $cookies = $session.Cookies.GetCookies($LoginEndpoint)
    foreach ($cookie in $cookies) {
        if ($cookie.name -eq 'csrf_access_token') {
            $CSRFToken = $cookie.value
        }
    }
    Write-Output $cookies
    Write-Output $CSRFToken
    $Headers = @{'X-CSRF-Token'=$CSRFToken}
}

$Request = @{
    "results" = @()
}
$Files = (Get-ChildItem -File -Path "$ResultsDir")
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

$JsonData = ConvertTo-Json -InputObject $Request
$ContentType = "application/json"

Write-Output "------------------SEND-RESULTS------------------"
$SendResultsEndpoint="$AllureServer/allure-docker-service/send-results?project_id=$Project"

if ($Force) {
    $SendResultsEndpoint+="&force_project_creation=true"
}

if ($Secure){
    $result = Invoke-WebRequest -Uri $SendResultsEndpoint -Method POST -ContentType $ContentType -Body $JsonData -UseBasicParsing -Headers $Headers -WebSession $session
} else {
    $result = Invoke-WebRequest -Uri $SendResultsEndpoint -Method POST -ContentType $ContentType -Body $JsonData -UseBasicParsing
}

Write-Output "Status Code:" $result.StatusCode
Write-Output "Response: " $result.Content

if ($Generate){

    $GenerateReportEndpoint="$AllureServer/allure-docker-service/generate-report?project_id=$Project"

    if ($ExecName){
        $GenerateReportEndpoint+="&execution_name=$ExecName"
    }

    if ($ExecFrom){
        $GenerateReportEndpoint+="&execution_from=$ExecFrom"
    }

    if ($ExecType){
        $GenerateReportEndpoint+="&execution_type=$ExecType"
    }

    if ($Secure){
        $result = Invoke-WebRequest -Uri $GenerateReportEndpoint -Method GET -UseBasicParsing -Headers $Headers -WebSession $session
    } else {
        $result = Invoke-WebRequest -Uri $GenerateReportEndpoint -Method GET -UseBasicParsing
    }

    Write-Output "Status Code:" $result.StatusCode
    Write-Output "Response: " $result.Content
    $ResultHash = $result.Content | ConvertFrom-Json
    $ReportURL = $ResultHash.data.report_url
    Write-Output "The generated report can be accessed on: $ReportURL"
}