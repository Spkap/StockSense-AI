const fs = require('fs');
const path = require('path');

function walk(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach(function(file) {
        file = path.join(dir, file);
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) { 
            results = results.concat(walk(file));
        } else { 
            if (file.endsWith('.tsx') || file.endsWith('.ts')) {
                results.push(file);
            }
        }
    });
    return results;
}

const files = walk('./src');
let changedCount = 0;

files.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let original = content;
    
    // Replace hardcoded px values with semantic text-micro
    content = content.replace(/text-\[8px\]/g, 'text-micro');
    content = content.replace(/text-\[9px\]/g, 'text-micro');
    content = content.replace(/text-\[10px\]/g, 'text-micro');
    content = content.replace(/text-\[11px\]/g, 'text-micro');
    
    // Replace text-xs with the semantic text-sm (12px in our design system)
    content = content.replace(/\btext-xs\b/g, 'text-sm');
    
    if (content !== original) {
        fs.writeFileSync(file, content);
        console.log(`[FIXED TYPOGRAPHY] ${file}`);
        changedCount++;
    }
});

console.log(`\nSuccess. Total files updated: ${changedCount}`);
