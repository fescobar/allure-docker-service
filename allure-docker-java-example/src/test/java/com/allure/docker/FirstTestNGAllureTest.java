package com.allure.docker;

import com.google.common.io.Files;
import io.qameta.allure.Allure;
import org.apache.commons.io.FileUtils;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.util.function.Supplier;

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
    public void test2(){
        System.out.println("test2");
        File file = new File(pathFile.getPath() +"/"+ "google.mp4");
        Allure.addStreamAttachmentAsync("Some video", "video/mp4", new Supplier<InputStream>() {
            @Override
            public InputStream get() {
                try {
                    return Files.asByteSource(file).openStream();
                } catch (IOException e) {
                    e.printStackTrace();
                }
                return null;
            }
        });
        Assert.fail("ERROR DURING THE TEST");
    }
}
