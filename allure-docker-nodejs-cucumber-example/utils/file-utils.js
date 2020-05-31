const fs = require('fs')

class FileUtils {
    static readFile(filePath) {
        return fs.readFileSync(filePath)
    }
}

module.exports = FileUtils;