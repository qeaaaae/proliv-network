const { execSync } = require('child_process');
const fs = require('fs');
const crypto = require('crypto');

const jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo";

const headers = [
    '-H', 'X-Forwarded-Proto: https',
    '-H', 'X-Forwarded-For: 127.0.0.1',
    '-H', `Authorization: Bearer ${jwt}`
];

// Get profiles
const result = execSync(`curl -s ${headers.join(' ')} http://localhost:3000/api/config-profiles`, { encoding: 'utf8' });
const data = JSON.parse(result);

let defaultProfile = null;
for (const p of data.response.configProfiles) {
    if (p.uuid === '00000000-0000-0000-0000-000000000000') {
        defaultProfile = p;
        break;
    }
}

if (!defaultProfile) {
    console.log('Default-Profile not found');
    process.exit(1);
}

console.log(`Found Default-Profile: ${defaultProfile.name}`);

const nlProfile = JSON.parse(JSON.stringify(defaultProfile));
nlProfile.uuid = crypto.randomUUID();
nlProfile.name = 'NL-Profile';
nlProfile.description = 'NL with WARP for AI';

const aiOutbound = {
    tag: 'ai-via-warp',
    protocol: 'socks',
    settings: {
        servers: [{
            address: '127.0.0.1',
            port: 40001
        }]
    }
};

const existingTags = (nlProfile.config.outbounds || []).map(o => o.tag);
if (!existingTags.includes('ai-via-warp')) {
    nlProfile.config.outbounds = nlProfile.config.outbounds || [];
    nlProfile.config.outbounds.push(aiOutbound);
    console.log('Added ai-via-warp outbound');
}

const routing = nlProfile.config.routing = nlProfile.config.routing || {};
const rules = routing.rules = routing.rules || [];

const geminiRule = {
    type: 'field',
    domain: ['geosite:category-ai-chat', 'generativelanguage.googleapis.com', 'gemini.google.com'],
    outboundTag: 'ai-via-warp'
};

const newRules = [];
let inserted = false;
for (const rule of rules) {
    if (!inserted && rule.type === 'field') {
        const domains = rule.domain || [];
        if (domains.some(d => d.toLowerCase().includes('google')) && !domains.some(d => d.toLowerCase().includes('youtube'))) {
            newRules.push(geminiRule);
            inserted = true;
        }
    }
    newRules.push(rule);
}

if (!inserted) {
    newRules.push(geminiRule);
}

routing.rules = newRules;
console.log('Added routing rule for Gemini API -> ai-via-warp');

// Write profile to temp file
const profileFile = `/tmp/nl_profile_${Date.now()}.json`;
fs.writeFileSync(profileFile, JSON.stringify(nlProfile));

// Create profile
const createHeaders = [...headers, '-H', 'Content-Type: application/json'];
const createCmd = `curl -s -X POST ${createHeaders.join(' ')} -d @${profileFile} http://localhost:3000/api/config-profiles`;
const createResult = execSync(createCmd, { encoding: 'utf8' });

console.log(`Create result: ${createResult.slice(0, 1000)}`);