package com.allure.docker;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.annotations.Test;

public class SecondTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(SecondTest.class.getName());

    @Test
    public void test3() {
        LOGGER.info("test3");
    }

    @Test
    public void test4(){
        LOGGER.info("test4");
    }
}
