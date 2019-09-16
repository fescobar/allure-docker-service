package com.allure.docker.steps;

import cucumber.api.java.en.Given;
import cucumber.api.java.en.Then;
import cucumber.api.java.en.When;
import org.junit.Assert;

public class StepsDefinitions {
    @Given("^I'm on a site$")
    public void imOnASite() {
    }

    @When("^I enter \"([^\"]*)\" on the page$")
    public void iEnterOnThePage(String arg1) {
    }

    @Then("^I verify is \"([^\"]*)\"$")
    public void i_verify_is(String status) throws Throwable {
        switch(status){
            case "FAILED":
                Assert.fail("FAILURE ON PURPOSE");
                break;

        }
    }

}
