package com.allure.docker;

import org.testng.annotations.Test;

import java.net.URL;

public class SecondTestNGAllureTest {
    private URL pathFile = SecondTestNGAllureTest.class.getResource("/files/");

    @Test
    public void test3() throws Exception{
        System.out.println("test1");
    }

    @Test
    public void test4(){
        System.out.println("test2");
    }
}
