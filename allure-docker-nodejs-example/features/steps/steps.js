const { Given, When, Then } = require('cucumber')
const chai = require('chai')
const expect = chai.expect;

Given('I\'m on a site', function () {

});

When('I enter {string} on the page', function (string) {

});

Then('I verify is {string}', function (status) {
    switch(status) {
        case "FAILED":
            expect.fail("FAILURE ON PURPOSE")
        break
        case "BROKEN":
                return 'pending'
    }
});