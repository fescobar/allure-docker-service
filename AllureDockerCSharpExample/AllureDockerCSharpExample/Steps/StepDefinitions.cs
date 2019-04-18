using TechTalk.SpecFlow;

namespace AllureDockerCSharpExample.Steps
{
    [Binding]
    public class StepDefinitions
    {
        [Given(@"I'm on a site")]
        public void GivenImOnASite()
        {
        }

        [When(@"I enter ""(.*)"" on the page")]
        public void WhenIEnterOnThePage(string p0)
        {
        }

        [Then(@"I verify is ok")]
        public void ThenIVerifyIsOk()
        {
        }
    }
}
