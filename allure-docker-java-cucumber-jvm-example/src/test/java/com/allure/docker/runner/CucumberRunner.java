package com.allure.docker.runner;

import cucumber.api.CucumberOptions;
import cucumber.api.junit.Cucumber;
import org.junit.runner.RunWith;

@RunWith(Cucumber.class)
@CucumberOptions(
        plugin = {"pretty", "html:target/cucumber", "junit:target/cucumber.xml", "io.qameta.allure.cucumberjvm.AllureCucumberJvm"},
        glue = {"com.allure.docker.steps"},
        features = "src/test/resources")
public class CucumberRunner {
}
