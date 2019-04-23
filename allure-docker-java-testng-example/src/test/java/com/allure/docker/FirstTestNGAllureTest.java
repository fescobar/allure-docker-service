package com.allure.docker;

import com.google.common.io.Files;
import io.qameta.allure.Allure;
import org.apache.commons.io.FileUtils;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.net.URL;

public class FirstTestNGAllureTest {
    private URL pathFile = FirstTestNGAllureTest.class.getResource("/files/");

    @Test
    public void test1() throws Exception{
        System.out.println("test1");
        File file = new File(pathFile.getPath() +"/"+ "fescobar.png");
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(FileUtils.readFileToByteArray(file));
        Allure.addAttachment("Some Screenshot",byteArrayInputStream);
    }

    @Test
    public void test2() throws IOException {
        System.out.println("test2");
        File file = new File(pathFile.getPath() +"/"+ "google.mp4");
        Allure.addAttachment("Some video", "video/mp4", Files.asByteSource(file).openStream(),"mp4");
        Assert.fail("ERROR DURING THE TEST");
    }
}