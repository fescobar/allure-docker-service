var CucumberJSAllureFormatter = require("cucumberjs-allure2-reporter").CucumberJSAllureFormatter;
var AllureRuntime = require("cucumberjs-allure2-reporter").AllureRuntime;
 
function Reporter(options) {
    CucumberJSAllureFormatter.call(this,
        options,
        new AllureRuntime({ resultsDir: "./allure-results" }),
        {});
}
Reporter.prototype = Object.create(CucumberJSAllureFormatter.prototype);
Reporter.prototype.constructor = Reporter;
 
exports.default = Reporter;