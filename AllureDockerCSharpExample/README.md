# C# DEMO PROJECT USING ALLURE

## INSTALLATION
- Install Microsoft Visual Studio 2017: https://docs.microsoft.com/en-us/visualstudio/releasenotes/vs2017-relnotes

- Add `msbuild.exe` path to `PATH` enviroment variable (Path according your local installation).
Example:
```sh
C:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise\MSBuild\15.0\Bin
```

- Add `vstest.console.exe` path to `PATH` enviroment variable (Path according your local installation).
Example:
```sh
C:\Program Files (x86)\Microsoft Visual Studio\2017\Enterprise\Common7\IDE\CommonExtensions\Microsoft\TestWindow
```

- Install dependencies executing next command:
```sh
./nuget.exe restore AllureDockerCSharpExample.sln -Verbosity Detailed -NonInteractive
 ```

- Build project executing next command:
```sh
msbuild.exe AllureDockerCSharpExample.sln
 ```

## USAGE
Execute Allure Docker Service from this directory
```sh
docker-compose up -d allure
```

- Verify if Allure report is working. Go to -> http://localhost:5050/allure-docker-service/latest-report

Each time you run tests, the Allure report will be updated.

Execute tests:
```sh
vstest.console.exe AllureDockerCSharpExample/bin/Debug/AllureDockerCSharpExample.dll /TestCaseFilter:"allure"
 ```

See documentation here: https://github.com/fescobar/allure-docker-service