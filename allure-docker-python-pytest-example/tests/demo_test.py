import pytest
import allure

@allure.epic('Allure Epic')
@allure.feature('Demo Feature')
@allure.story('Passed Example')
@allure.issue('https://example.org/issue/1')
@allure.testcase('https://example.org/tms/2')
def test_passed_scenario():
    """
    Passed Scenario
    """
    with allure.step("Given I'm on a site"):
        print('step1')
    with allure.step("When I enter something on the page"):
        print('step2')
    with allure.step("Then I verify is OK"):
        print('step3')

@allure.epic('Allure Epic')
@allure.feature('Demo Feature')
@allure.story('Failed Example')
@allure.issue('https://example.org/issue/3')
@allure.testcase('https://example.org/tms/4')
def test_failed_scenario():
    """
    Failed Scenario
    """
    with allure.step("Given I'm on a site"):
        print('step1')
    with allure.step("When I enter something on the page"):
        print('step2')
    with allure.step("Then I verify is FAILED"):
        print('step3')
        pytest.fail('FAILURE ON PURPOSE')

@allure.epic('Allure Epic')
@allure.feature('Demo Feature')
@allure.story('bROKEN Example')
@allure.issue('https://example.org/issue/5')
@allure.testcase('https://example.org/tms/6')
def test_broken_scenario():
    """
    Broken Scenario
    """
    with allure.step("Given I'm on a site"):
        print('step1')
    with allure.step("When I enter something on the page"):
        print('step2')
    with allure.step("Then I verify is BROKEN"):
        print('step3')
        raise NotImplementedError('NOT IMPLEMENTED')

@pytest.fixture(autouse=True)
def hooks():
    # set up

    yield
    # tear down
    f = open('./files/fescobar.png', "rb")
    image = f.read()
    allure.attach(
        image,
        name = 'image',
        attachment_type = allure.attachment_type.PNG
    )

    f = open('./files/google.mp4', "rb")
    image = f.read()
    allure.attach(
        image,
        name = 'image',
        attachment_type = allure.attachment_type.MP4
    )