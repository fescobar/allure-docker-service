package com.allure.docker;

import org.testng.annotations.Factory;

public class FourthTestFactory {
    @Factory
    public Object[] factoryMethod() {
        return new Object[] {
                new FourthTest(1),
                new FourthTest(2),
                new FourthTest(3),
                new FourthTest(4)
        };
    }
}
