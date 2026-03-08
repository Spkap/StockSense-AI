import { readdirSync, statSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

function walk(dir: string): string[] {
    let results: string[] = [];
    const list = readdirSync(dir);
    list.forEach(function(file) {
        file = join(dir, file);
        const stat = statSync(file);
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
    let content = readFileSync(file, 'utf8');
    let original = content;
    
    // Replace hardcoded px values with semantic text-micro
    content = content.replace(/text-\[8px\]/g, 'text-micro');
    content = content.replace(/text-\[9px\]/g, 'text-micro');
    content = content.replace(/text-\[10px\]/g, 'text-micro');
    content = content.replace(/text-\[11px\]/g, 'text-micro');
    
    // Replace text-xs with the semantic text-sm (12px in our design system)
    content = content.replace(/\btext-xs\b/g, 'text-sm');
    
    if (content !== original) {
        writeFileSync(file, content);
        console.log(`[FIXED TYPOGRAPHY] ${file}`);
        changedCount++;
    }
});

console.log(`\nSuccess. Total files updated: ${changedCount}`);
