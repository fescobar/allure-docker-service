package com.allure.docker;

import io.qameta.allure.testng.TestInstanceParameter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.annotations.Test;

public class FourthTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(FourthTest.class.getName());
    @TestInstanceParameter("Iteration")
    private int param;

    public FourthTest(int param) {
        this.param = param;
    }

    @Test
    public void test8() {
        LOGGER.info("test8 ->" + param);
    }

}
