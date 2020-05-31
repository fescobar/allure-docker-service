import { allure } from 'allure-mocha/runtime';
import { ContentType } from 'allure-js-commons';
import { FileUtils } from "@utils/file-utils"
import { expect } from 'chai'

describe('Multiple Data Example', async function() {
  beforeEach(function() {
    allure.epic('My Epic');
    allure.feature('Demo Allure')
  });
  
  let dataObjects = [
    { data: 'something', status: 'OK'},
    { data: 'something2', status: 'FAILED'},
    { data: 'something3', status: 'BROKEN'}
  ];

  for(let dataObject  of dataObjects) {
    let item = dataObject

    it(`Multiple Data Example - ${item.status}`, async () => {
      allure.parameter('data', JSON.stringify(item))
      
      await allure.step('I\'m on a site', async () => {
        console.log('I\'m on a site')
      })

      await allure.step(`I verify is <${item.data}>`, async () => {
        console.log(`I verify is ${item.data}`)
      })

      await allure.step(`I verify is <${item.status}>`, async () => {
        let img = FileUtils.readFile('./resources/fescobar.png')
        allure.attachment('any_image', img, ContentType.PNG)
      
        let video = FileUtils.readFile('./resources/google.mp4')
        allure.attachment('any_video', video, ContentType.WEBM)
        
        switch(item.status) {
          case "FAILED":
              expect.fail("FAILURE ON PURPOSE")
          break
          case "BROKEN":
              throw new Error('BROKEN')
      }
      })
    })
  }

});
