const { After } = require('cucumber');
const fs = require('fs');

After({}, async function () {
    let img = fs.readFileSync('./resources/fescobar.png');
    this.attach(img, 'image/png');

    let video = fs.readFileSync('./resources/google.mp4');
    this.attach(video, 'video/webm');
});
