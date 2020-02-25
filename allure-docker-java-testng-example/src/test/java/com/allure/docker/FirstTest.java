package com.allure.docker;

import com.google.common.io.Files;
import io.qameta.allure.Allure;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;

public class FirstTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(FirstTest.class.getName());

    private URL pathResources = FirstTest.class.getResource("/files/");

    @Test
    public void test1() throws Exception {
        LOGGER.info("test1");
        ByteArrayInputStream imageAsByteArrayIS = new ByteArrayInputStream(FileUtils.readFileToByteArray(new File(pathResources.getPath() +"/"+ "fescobar.png")));

        Allure.addAttachment("Some Screenshot", imageAsByteArrayIS);
    }

    @Test
    public void test2() throws IOException {
        LOGGER.info("test2");
        InputStream videoAsInputStream = Files.asByteSource(new File(pathResources.getPath() +"/"+ "google.mp4")).openStream();

        Allure.addAttachment("Some video", "video/mp4", videoAsInputStream,"mp4");

        Assert.fail("FAILURE ON PURPOSE");
    }
}