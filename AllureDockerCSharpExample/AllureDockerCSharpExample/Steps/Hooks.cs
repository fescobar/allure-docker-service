using System.IO;
using System.Reflection;
using System.Text;
using Allure.Commons;
using NUnit.Framework;
using TechTalk.SpecFlow;

namespace AllureDockerCSharpExample.Steps
{
    [Binding]
    public class Hooks
    {
        private static string resourcesDirectoryPath = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), @"Resources\");

        [AfterScenario(Order = int.MinValue)]
        public void AfterScenario()
        {
            string scenarioName = TestContext.CurrentContext.Test.Name;

            AllureLifecycle.Instance.UpdateTestCase(tc =>
            {
                tc.name = scenarioName;
                tc.historyId = TestContext.CurrentContext.Test.FullName;
            });

            string content = "any content";
            AllureLifecycle.Instance.AddAttachment("Any Content", "text/plain", Encoding.ASCII.GetBytes(content), ".txt");

            string url = "https://www.linkedin.com/in/fescobarsystems";
            AllureLifecycle.Instance.UpdateTestCase(tc =>
            {
                tc.links.Add(new Link()
                {
                    name = "Any Link",
                    url = url
                });
            });

            byte[] screenshot = File.ReadAllBytes(resourcesDirectoryPath + "/" + "fescobar.png");
            AllureLifecycle.Instance.AddAttachment(scenarioName, "image/png", screenshot, ".png");

            byte[] video = File.ReadAllBytes(resourcesDirectoryPath + "/" + "google.mp4");
            AllureLifecycle.Instance.AddAttachment(scenarioName, "video/mp4", video);
        }
    }
}
