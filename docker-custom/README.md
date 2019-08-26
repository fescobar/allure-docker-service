# Build custom image

To build your custom image execute the following command from the root of the project.

```shell script
docker build --no-cache --build-arg BUILD_DATE=$(date +"%Y-%m-%dT%H:%M:%SZ") --file ./docker-custom/Dockerfile.bionic-custom --tag allure-docker-service:build .
```

To customize your image, modify the `Dockerfile.bionic-custom` as needed and (re-)run the command.

__note:__ the `Dockerfile.bionic-custom` has default arguments set, which you can change in the Dockerfile.bionic-custom or override by --build-arg.