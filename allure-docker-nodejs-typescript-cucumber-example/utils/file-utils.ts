const fs = require('fs')

export class FileUtils {
    static readFile(filePath: string): any {
        return fs.readFileSync(filePath)
    }
}