const { After } = require('cucumber')
const FileUtils = require('@utils/file-utils')

After({}, async function () {
    let img = FileUtils.readFile('./resources/fescobar.png')
    this.attach(img, 'image/png')

    let video = FileUtils.readFile('./resources/google.mp4')
    this.attach(video, 'video/webm')
});
