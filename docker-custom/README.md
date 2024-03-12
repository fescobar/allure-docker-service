# Build custom image

To build your custom image execute the following command from the root of the project.

```shell script
docker build --no-cache --build-arg BUILD_DATE=$(date +"%Y-%m-%dT%H:%M:%SZ") --file ./docker-custom/Dockerfile.custom --tag allure-docker-service:build .
```

To customize your image, modify the `Dockerfile.custom` as needed and (re-)run the command.

__note:__ the `Dockerfile.custom` has default arguments set, which you can change in the Dockerfile.custom or override by --build-arg.