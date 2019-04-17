Feature: Demo Allure

    Scenario: Simple Scenario
        Given I'm on a site
        When I enter "something" on the page
        Then I verify is ok


    Scenario Outline: Outline Scenario
        Given I'm on a site
        When I enter <data> on the page
        Then I verify is ok
        Examples:
            | data          |
            | "something"   |
            | "something2"   |
