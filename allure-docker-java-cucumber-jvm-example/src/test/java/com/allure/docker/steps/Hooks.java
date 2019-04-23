package com.allure.docker.steps;

import cucumber.api.Scenario;
import cucumber.api.java.Before;
import io.qameta.allure.Allure;
import org.apache.commons.io.FileUtils;
import com.google.common.io.Files;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.net.URL;

public class Hooks {
    private URL pathFile = Hooks.class.getResource("/files/");

    @Before
    public void afterScenario(Scenario scenario) throws IOException {
        File image = new File(pathFile.getPath() + "/" + "fescobar.png");
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(FileUtils.readFileToByteArray(image));
        Allure.addAttachment("Some Screenshot", byteArrayInputStream);

        File video = new File(pathFile.getPath() + "/" + "google.mp4");
        Allure.addAttachment("Some video", "video/mp4", Files.asByteSource(video).openStream(), "mp4");
    }
}
