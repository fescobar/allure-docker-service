package com.allure.docker.listeners;

import com.allure.docker.FirstTest;
import io.qameta.allure.Allure;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.net.URL;

public class MyListener implements ITestListener {
    private static final Logger LOGGER = LoggerFactory.getLogger(MyListener.class.getName());
    private URL pathResources = FirstTest.class.getResource("/files/");

    @Override
    public void onTestStart(ITestResult iTestResult) {

    }

    @Override
    public void onTestSuccess(ITestResult iTestResult) {
        LOGGER.info("onTestSuccess - listener");
        byte[] bytes = null;

        try {
            bytes = FileUtils.readFileToByteArray(new File(pathResources.getPath() + "/" + "fescobar.png"));
        } catch (Exception ex) {
            LOGGER.error("Error during reading file", ex);
        }

        ByteArrayInputStream imageAsByteArrayIS = new ByteArrayInputStream(bytes);

        Allure.addAttachment("Some Screenshot from listener", imageAsByteArrayIS);
    }

    @Override
    public void onTestFailure(ITestResult iTestResult)  {

    }

    @Override
    public void onTestSkipped(ITestResult iTestResult) {

    }

    @Override
    public void onTestFailedButWithinSuccessPercentage(ITestResult iTestResult) {

    }

    @Override
    public void onStart(ITestContext iTestContext) {

    }

    @Override
    public void onFinish(ITestContext iTestContext) {

    }
}
