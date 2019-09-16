@allure
Feature: Demo Allure

  Scenario: Single Example
    Given I'm on a site
    When I enter "something" on the page
    Then I verify is "OK"


  Scenario Outline: Multiple Data Example
    Given I'm on a site
    When I enter <data> on the page
    Then I verify is <status>
    Examples:
      | data          | status  |
      | "something"   | "OK"      |
      | "something2"  | "FAILED"  |