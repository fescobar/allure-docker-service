import { After } from "cucumber"
import { FileUtils } from "@utils/file-utils"

After({}, async function () {
    let img = FileUtils.readFile('./resources/fescobar.png')
    this.attach(img, 'image/png')

    let video = FileUtils.readFile('./resources/google.mp4')
    this.attach(video, 'video/webm')
});
