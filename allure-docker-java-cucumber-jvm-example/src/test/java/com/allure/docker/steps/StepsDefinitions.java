package com.allure.docker.steps;

import cucumber.api.java.en.Given;
import cucumber.api.java.en.Then;
import cucumber.api.java.en.When;

public class StepsDefinitions {
    @Given("^I'm on a site$")
    public void imOnASite() {
    }

    @When("^I enter \"([^\"]*)\" on the page$")
    public void iEnterOnThePage(String arg1) {
    }

    @Then("^I verify is ok$")
    public void iVerifyIsOk() {
    }
}
